"""Pre-check → clarify (check each KR, ask about vague ones) → decompose per KR (parallel) →
dedup over the whole plan → validate.

The pipeline is bound to one provider for the whole run and never switches provider on
failure: sending OKR data to another vendor needs the user's explicit choice.
"""

import asyncio
import inspect
import logging
import time
import weakref
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from app.planner_llm.language import detect_language
from app.planner_llm.precheck import run_precheck
from app.planner_llm.prompts import (
    clarify_prompt,
    decompose_prompt,
    dedup_prompt,
    key_result_check_prompt,
    key_result_needs_prompt,
    link_prompt,
    with_feedback,
)
from app.planner_llm.providers.base import LLMProvider, PipelineStep, Prompt
from app.planner_llm.providers.errors import (
    InvalidJSONError,
    ProviderError,
    ProviderTimeoutError,
)
from app.planner_llm.schemas import (
    ClarifyOutput,
    ClarifyQuestion,
    DecomposeOutput,
    DedupOutput,
    KeyResultCheck,
    KeyResultInput,
    KeyResultNeed,
    KeyResultNeedsOutput,
    Language,
    LinkOutput,
    ObjectiveInput,
    OkrInput,
    PipelineError,
    PipelineFailure,
    PipelineResult,
    PlannedTask,
    ProgressEvent,
    RunTrace,
    StageName,
    StepTrace,
    TimeBudget,
)
from app.planner_llm.validation import (
    MAX_DEDUP_CROSS_DEPENDENCIES,
    MAX_DEDUP_MERGES,
    MAX_QUESTIONS,
    apply_dedup,
    clarify_errors,
    decompose_errors,
    kr_hours_cap,
    link_errors,
    namespace_tasks,
    need_errors,
    ok_with_questions_as_clarification,
    plan_quality_errors,
    rebalance_caps,
    task_graph_errors,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[ProgressEvent], Awaitable[None] | None]
M = TypeVar("M", bound=BaseModel)
_T = TypeVar("_T")
ResultStatus = Literal["ok", "needs_clarification", "invalid_input"]

# The OpenAI SDK already retries its own timeouts; a local call gets one retry here, and it
# uses one of the ``max_retries`` attempts so the worst-case run time stays bounded.
_TIMEOUT_RETRY_PROVIDERS = frozenset({"local"})
_MAX_TIMEOUT_RETRIES = 1
_STAGE_ORDER: tuple[StageName, ...] = ("precheck", "clarify", "decompose", "dedup", "validate")
_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict[str, asyncio.Semaphore]]"
_semaphores = weakref.WeakKeyDictionary()


def provider_semaphore(provider: LLMProvider) -> asyncio.Semaphore:
    """One semaphore per provider name and event loop, shared by concurrent plan runs."""
    per_loop = _semaphores.setdefault(asyncio.get_running_loop(), {})
    if provider.name not in per_loop:
        per_loop[provider.name] = asyncio.Semaphore(max(1, provider.max_concurrency))
    return per_loop[provider.name]


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _measurable(kr: KeyResultInput) -> bool:
    """A metric with its baseline and target is a number to reach, so the KR is concrete."""
    return kr.metric is not None and kr.baseline is not None and kr.target is not None


def _across_key_results(out: DedupOutput, tasks: Sequence[PlannedTask]) -> DedupOutput:
    """Keep the review to what it is asked for: links and duplicates between key results.

    It only sees titles, so it cannot know the order already set inside a key result.
    """
    kr_of = {t.local_id: t.kr_id for t in tasks}

    def one_kr(ids: Sequence[str]) -> bool:
        return all(tid in kr_of for tid in ids) and len({kr_of[tid] for tid in ids}) == 1

    merges = [m for m in out.merges if not one_kr([m.keep_id, *m.remove_ids])]
    deps = [d for d in out.cross_dependencies if not one_kr([d.task_id, d.depends_on_id])]
    return DedupOutput(
        merges=merges[:MAX_DEDUP_MERGES],
        cross_dependencies=deps[:MAX_DEDUP_CROSS_DEPENDENCIES],
    )


def _linked(tasks: Sequence[PlannedTask], kr_id: str, needs_kr_id: str) -> bool:
    kr_of = {t.local_id: t.kr_id for t in tasks}
    return any(
        kr_of.get(dep) == needs_kr_id for t in tasks if t.kr_id == kr_id for dep in t.depends_on
    )


def _validation_messages(exc: ValidationError) -> list[str]:
    messages = []
    for err in exc.errors(include_input=False, include_url=False):
        loc = ".".join(str(part) for part in err["loc"]) or "<root>"
        messages.append(f"{loc}: {err['msg']}")
    return messages


class _Run:
    def __init__(
        self,
        okr: OkrInput,
        provider: LLMProvider,
        *,
        max_retries: int,
        on_progress: ProgressCallback | None,
        decomposed: dict[str, list[PlannedTask]] | None = None,
        budget: TimeBudget | None = None,
    ) -> None:
        self.okr = okr
        self.provider = provider
        self.budget = budget
        self.max_retries = max(0, max_retries)
        self.on_progress = on_progress
        self.decomposed = decomposed if decomposed is not None else {}
        self.language: Language = okr.language or detect_language(okr)
        self.steps: list[StepTrace] = []
        self.stage_ms: dict[str, int] = {}
        self.models: dict[str, str] = {}
        self.started = time.perf_counter()
        self.semaphore = provider_semaphore(provider)
        self.kr_order = {
            kr.id: (oi, ki)
            for oi, o in enumerate(okr.objectives)
            for ki, kr in enumerate(o.key_results)
        }
        self.objective_order = {o.id: oi for oi, o in enumerate(okr.objectives)}

    async def emit(self, event: ProgressEvent) -> None:
        if self.on_progress is None:
            return
        try:
            result = self.on_progress(event)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.warning("progress callback failed stage=%s", event.stage, exc_info=True)

    def trace(self) -> RunTrace:
        def sort_key(step: StepTrace) -> tuple[int, int, int]:
            if step.kr_id in self.kr_order:
                oi, ki = self.kr_order[step.kr_id]
            else:
                oi, ki = self.objective_order.get(step.objective_id or "", -1), -1
            return _STAGE_ORDER.index(step.step), oi, ki

        steps = sorted(self.steps, key=sort_key)
        return RunTrace(
            provider=self.provider.name,
            models=dict(self.models),
            total_retries=sum(s.retries for s in steps),
            stage_duration_ms=dict(self.stage_ms),
            duration_ms=_elapsed_ms(self.started),
            steps=steps,
        )

    async def fail(self, failure: PipelineFailure) -> PipelineError:
        await self.emit(
            ProgressEvent(
                stage=failure.step,
                status="failed",
                objective_id=failure.objective_id,
                kr_id=failure.kr_id,
                attempt=failure.attempts or None,
            )
        )
        logger.warning(
            "planner pipeline failed code=%s step=%s kr_id=%s attempts=%d provider=%s model=%s",
            failure.code,
            failure.step,
            failure.kr_id,
            failure.attempts,
            failure.provider,
            failure.model,
        )
        return PipelineError(failure, self.trace())

    def retries_timeout(self, exc: ProviderError, *, timeouts: int, attempt: int) -> bool:
        return (
            isinstance(exc, ProviderTimeoutError)
            and self.provider.name in _TIMEOUT_RETRY_PROVIDERS
            and timeouts < _MAX_TIMEOUT_RETRIES
            and attempt < self.max_retries
        )

    async def call(
        self,
        *,
        stage: StageName,
        step: PipelineStep,
        system: str,
        user: str,
        schema: type[M],
        check: Callable[[M], list[str]],
        objective_id: str | None = None,
        kr_id: str | None = None,
        salvage: Callable[[M], M | None] | None = None,
    ) -> M:
        """Call the model until ``check`` passes or retries run out.

        ``salvage`` may turn the last schema-valid output into an acceptable one once retries
        are spent; returning ``None`` keeps the ``invalid_llm_output`` failure.
        """
        model = self.provider.model_for(step)
        self.models[step] = model
        trace = StepTrace(step=stage, model=model, objective_id=objective_id, kr_id=kr_id)
        started = time.perf_counter()
        errors: list[str] = []
        previous: dict[str, Any] | None = None
        last_parsed: M | None = None
        timeouts = 0

        for attempt in range(self.max_retries + 1):
            trace.attempts = attempt + 1
            trace.retries = attempt
            if attempt:
                await self.emit(
                    ProgressEvent(
                        stage=stage,
                        status="retry",
                        objective_id=objective_id,
                        kr_id=kr_id,
                        attempt=attempt + 1,
                    )
                )
            prompt = Prompt(
                step=step,
                system=system,
                user=with_feedback(user, errors, previous) if errors else user,
                objective_id=objective_id,
                kr_id=kr_id,
                attempt=attempt,
            )
            try:
                async with self.semaphore:
                    raw = await self.provider.generate_json(prompt, schema)
            except InvalidJSONError as exc:
                errors = [f"response is not valid JSON ({exc})"]
                previous = None
            except ProviderError as exc:
                if self.retries_timeout(exc, timeouts=timeouts, attempt=attempt):
                    timeouts += 1
                    trace.errors.append(f"attempt {attempt + 1}: {exc}")
                    logger.info(
                        "llm call timed out, retrying step=%s kr_id=%s attempt=%d",
                        stage,
                        kr_id,
                        attempt + 1,
                    )
                    continue
                trace.errors.append(str(exc))
                trace.duration_ms = _elapsed_ms(started)
                self.steps.append(trace)
                raise await self.fail(
                    PipelineFailure(
                        code="provider_unavailable",
                        step=stage,
                        message=str(exc) or type(exc).__name__,
                        provider=self.provider.name,
                        model=model,
                        objective_id=objective_id,
                        kr_id=kr_id,
                        attempts=attempt + 1,
                        errors=[str(exc)],
                        suggestions=["check_connection", "switch_provider"],
                    )
                ) from exc
            else:
                previous = raw
                try:
                    parsed = schema.model_validate(raw)
                except ValidationError as exc:
                    errors = _validation_messages(exc)
                else:
                    last_parsed = parsed
                    errors = check(parsed)
                    if not errors:
                        trace.duration_ms = _elapsed_ms(started)
                        self.steps.append(trace)
                        logger.info(
                            "llm step ok step=%s kr_id=%s model=%s attempts=%d duration_ms=%d",
                            stage,
                            kr_id,
                            model,
                            trace.attempts,
                            trace.duration_ms,
                        )
                        return parsed
            trace.errors.extend(f"attempt {attempt + 1}: {e}" for e in errors)
            logger.info(
                "llm output rejected step=%s kr_id=%s attempt=%d errors=%d",
                stage,
                kr_id,
                attempt + 1,
                len(errors),
            )

        trace.duration_ms = _elapsed_ms(started)
        self.steps.append(trace)
        salvaged = salvage(last_parsed) if salvage and last_parsed is not None else None
        if salvaged is not None:
            logger.info(
                "llm output salvaged after retries step=%s kr_id=%s model=%s attempts=%d",
                stage,
                kr_id,
                model,
                trace.attempts,
            )
            return salvaged
        raise await self.fail(
            PipelineFailure(
                code="invalid_llm_output",
                step=stage,
                message=f"model output still invalid after {self.max_retries} retries",
                provider=self.provider.name,
                model=model,
                objective_id=objective_id,
                kr_id=kr_id,
                attempts=trace.attempts,
                errors=errors,
                suggestions=["switch_model", "switch_provider"],
            )
        )

    async def run(self, *, skip_clarification: bool) -> PipelineResult:
        stage_started = time.perf_counter()
        await self.emit(ProgressEvent(stage="precheck", status="started"))
        pre = run_precheck(self.okr, self.language)
        self.stage_ms["precheck"] = _elapsed_ms(stage_started)
        self.steps.append(StepTrace(step="precheck", duration_ms=self.stage_ms["precheck"]))
        await self.emit(
            ProgressEvent(
                stage="precheck", status="completed", duration_ms=self.stage_ms["precheck"]
            )
        )
        if pre.issues:
            return self.result("invalid_input", issues=pre.issues)

        if skip_clarification:
            await self.emit(ProgressEvent(stage="clarify", status="skipped"))
        else:
            questions = [
                ClarifyQuestion(
                    id="", kr_id=g.kr_id, question=g.question, reason=g.reason, source="precheck"
                )
                for g in pre.metric_gaps
            ]
            questions += await self.clarify(questions)
            if questions:
                questions = [
                    q.model_copy(update={"id": f"q{i}"})
                    for i, q in enumerate(questions[:MAX_QUESTIONS], start=1)
                ]
                return self.result("needs_clarification", questions=questions)

        tasks = await self.decompose_all()
        tasks = await self.dedup_all(tasks)
        await self.validate(tasks)
        return self.result("ok", tasks=tasks)

    async def clarify(self, already_asked: Sequence[ClarifyQuestion]) -> list[ClarifyQuestion]:
        """Judge each key result on its own, then ask only about the vague ones.

        One verdict per key result is far more reliable with small local models than judging
        the whole OKR in one answer, which tends to flag clear key results at random.
        """
        stage_started = time.perf_counter()
        await self.emit(ProgressEvent(stage="clarify", status="started"))
        covered = {q.kr_id for q in already_asked}
        pairs = [
            (o, kr)
            for o in self.okr.objectives
            for kr in o.key_results
            if kr.id not in covered and not _measurable(kr)
        ]
        verdicts = await self.gather([self.check_key_result(o, kr) for o, kr in pairs])
        room = MAX_QUESTIONS - len(already_asked)
        vague = [kr for (_, kr), concrete in zip(pairs, verdicts, strict=True) if not concrete]
        questions = await self.ask(vague[: max(0, room)])
        self.stage_ms["clarify"] = _elapsed_ms(stage_started)
        await self.emit(
            ProgressEvent(stage="clarify", status="completed", duration_ms=self.stage_ms["clarify"])
        )
        return questions

    async def check_key_result(self, objective: ObjectiveInput, kr: KeyResultInput) -> bool:
        system, user = key_result_check_prompt(self.okr, kr)
        output = await self.call(
            stage="clarify",
            step="clarify",
            system=system,
            user=user,
            schema=KeyResultCheck,
            check=lambda out: [],
            objective_id=objective.id,
            kr_id=kr.id,
        )
        return output.concrete

    async def ask(self, vague: Sequence[KeyResultInput]) -> list[ClarifyQuestion]:
        if not vague:
            return []
        vague_ids = [kr.id for kr in vague]
        system, user = clarify_prompt(self.okr, self.language, vague)
        output = await self.call(
            stage="clarify",
            step="clarify",
            system=system,
            user=user,
            schema=ClarifyOutput,
            check=lambda out: clarify_errors(out, vague_ids, required=vague_ids),
            salvage=lambda out: ok_with_questions_as_clarification(out, vague_ids),
        )
        if output.status == "ok":
            return []
        return [
            ClarifyQuestion(
                id="",
                kr_id=q.kr_id,
                question=q.question.strip(),
                reason=q.reason.strip(),
                source="llm",
            )
            for q in output.questions
        ]

    async def decompose_all(self) -> list[PlannedTask]:
        """Plan every KR within its share of the budget, then cut the KRs that overshoot it.

        The first pass lets a heavy KR take more than an equal share; when the plan as a whole
        no longer fits the quarter, the KRs above an equal share are planned once more with
        tighter caps that add up to the budget.
        """
        stage_started = time.perf_counter()
        pairs = [(o, kr) for o in self.okr.objectives for kr in o.key_results]
        total = len(pairs)
        done = 0
        cap = None if self.budget is None else kr_hours_cap(self.budget.usable_hours, total)
        await self.emit(
            ProgressEvent(stage="decompose", status="started", completed=0, total=total)
        )

        async def one(
            objective: ObjectiveInput,
            kr: KeyResultInput,
            max_hours: float | None,
            *,
            replan: bool = False,
        ) -> list[PlannedTask]:
            nonlocal done
            if kr.id in self.decomposed and not replan:
                done += 1
                await self.emit(
                    ProgressEvent(
                        stage="decompose",
                        status="completed",
                        objective_id=objective.id,
                        kr_id=kr.id,
                        completed=done,
                        total=total,
                        duration_ms=0,
                    )
                )
                return self.decomposed[kr.id]
            kr_started = time.perf_counter()
            await self.emit(
                ProgressEvent(
                    stage="decompose",
                    status="started",
                    objective_id=objective.id,
                    kr_id=kr.id,
                    completed=done,
                    total=total,
                )
            )
            system, user = decompose_prompt(
                self.okr, objective, kr, self.language, self.budget, max_hours
            )
            output = await self.call(
                stage="decompose",
                step="decompose",
                system=system,
                user=user,
                schema=DecomposeOutput,
                check=lambda out: [
                    *decompose_errors(out, kr.id),
                    *plan_quality_errors(out.tasks, max_hours),
                ],
                objective_id=objective.id,
                kr_id=kr.id,
                salvage=lambda out: None if decompose_errors(out, kr.id) else out,
            )
            tasks = namespace_tasks(output, kr_id=kr.id, objective_id=objective.id)
            self.decomposed[kr.id] = tasks
            if not replan:
                done += 1
            await self.emit(
                ProgressEvent(
                    stage="decompose",
                    status="completed",
                    objective_id=objective.id,
                    kr_id=kr.id,
                    completed=done,
                    total=total,
                    duration_ms=_elapsed_ms(kr_started),
                )
            )
            return tasks

        await self.gather([one(o, kr, cap) for o, kr in pairs])
        if self.budget is not None:
            hours = {
                kr.id: sum(t.estimate_hours for t in self.decomposed[kr.id]) for _, kr in pairs
            }
            caps = rebalance_caps(hours, self.budget.usable_hours)
            if caps:
                logger.info(
                    "plan over budget, re-planning krs=%d total_hours=%g usable_hours=%g",
                    len(caps),
                    sum(hours.values()),
                    self.budget.usable_hours,
                )
                await self.gather(
                    [one(o, kr, caps[kr.id], replan=True) for o, kr in pairs if kr.id in caps]
                )
        self.stage_ms["decompose"] = _elapsed_ms(stage_started)
        return [task for _, kr in pairs for task in self.decomposed[kr.id]]

    async def dedup_all(self, tasks: list[PlannedTask]) -> list[PlannedTask]:
        """One call over the whole plan, so links between objectives can be found too."""
        stage_started = time.perf_counter()
        kr_ids = list(self.kr_order)
        if len(kr_ids) < 2:
            await self.emit(ProgressEvent(stage="dedup", status="skipped"))
            return tasks
        await self.emit(ProgressEvent(stage="dedup", status="started", completed=0, total=1))
        applied: list[PlannedTask] = tasks

        def check(out: DedupOutput) -> list[str]:
            nonlocal applied
            applied, errors = apply_dedup(tasks, _across_key_results(out, tasks), kr_ids)
            return errors

        def keep_plan(out: DedupOutput) -> DedupOutput:
            nonlocal applied
            applied = tasks
            return DedupOutput(merges=[], cross_dependencies=[])

        system, user = dedup_prompt(self.okr, tasks)
        await self.call(
            stage="dedup",
            step="dedup",
            system=system,
            user=user,
            schema=DedupOutput,
            check=check,
            salvage=keep_plan,
        )
        applied = await self.link_needs(applied)
        self.stage_ms["dedup"] = _elapsed_ms(stage_started)
        await self.emit(
            ProgressEvent(
                stage="dedup",
                status="completed",
                completed=1,
                total=1,
                duration_ms=self.stage_ms["dedup"],
            )
        )
        return applied

    async def link_needs(self, tasks: list[PlannedTask]) -> list[PlannedTask]:
        """Add the links between key results that the plan-wide review missed.

        Small local models rarely spot them among dozens of tasks, so this asks two smaller
        questions: which key result needs which (texts only), then which two tasks carry each
        need. Answers that keep breaking the rules add no link instead of failing the plan.
        """
        kr_ids = list(self.kr_order)

        def valid_needs(out: KeyResultNeedsOutput) -> KeyResultNeedsOutput:
            needs = [
                n for n in out.needs if not need_errors(KeyResultNeedsOutput(needs=[n]), kr_ids)
            ]
            return KeyResultNeedsOutput(needs=needs)

        system, user = key_result_needs_prompt(self.okr)
        output = await self.call(
            stage="dedup",
            step="dedup",
            system=system,
            user=user,
            schema=KeyResultNeedsOutput,
            check=lambda out: need_errors(out, kr_ids),
            salvage=valid_needs,
        )
        for need in output.needs:
            if not _linked(tasks, need.kr_id, need.needs_kr_id):
                tasks = await self.link(need, tasks)
        return tasks

    async def link(self, need: KeyResultNeed, tasks: list[PlannedTask]) -> list[PlannedTask]:
        needing = [t for t in tasks if t.kr_id == need.kr_id]
        giving = [t for t in tasks if t.kr_id == need.needs_kr_id]
        applied = tasks

        def check(out: LinkOutput) -> list[str]:
            nonlocal applied
            errors = link_errors(out, [t.local_id for t in needing], [t.local_id for t in giving])
            if errors:
                return errors
            dedup = DedupOutput(merges=[], cross_dependencies=out.links)
            applied, errors = apply_dedup(tasks, dedup, list(self.kr_order))
            return errors

        system, user = link_prompt(need, needing, giving)
        await self.call(
            stage="dedup",
            step="dedup",
            system=system,
            user=user,
            schema=LinkOutput,
            check=check,
            salvage=lambda out: LinkOutput(links=[]),
        )
        return applied

    async def validate(self, tasks: list[PlannedTask]) -> None:
        stage_started = time.perf_counter()
        kr_ids = list(self.kr_order)
        errors = task_graph_errors(tasks, allowed_kr_ids=kr_ids, required_kr_ids=kr_ids)
        owner = {kr.id: o.id for o in self.okr.objectives for kr in o.key_results}
        errors += [
            f"task {t.local_id}: objective_id does not own kr_id {t.kr_id}"
            for t in tasks
            if owner.get(t.kr_id) != t.objective_id
        ]
        self.stage_ms["validate"] = _elapsed_ms(stage_started)
        self.steps.append(
            StepTrace(step="validate", duration_ms=self.stage_ms["validate"], errors=errors)
        )
        if errors:
            raise await self.fail(
                PipelineFailure(
                    code="internal_validation",
                    step="validate",
                    message="combined plan failed validation",
                    provider=self.provider.name,
                    errors=errors,
                    suggestions=["switch_model", "switch_provider"],
                )
            )

    @staticmethod
    async def gather(coros: list[Coroutine[Any, Any, _T]]) -> list[_T]:
        """Run in parallel; the first failure cancels the rest so no budget is wasted."""
        try:
            async with asyncio.TaskGroup() as group:
                futures = [group.create_task(c) for c in coros]
        except BaseExceptionGroup as eg:
            for exc in eg.exceptions:
                if isinstance(exc, PipelineError):
                    raise exc from None
            raise
        return [f.result() for f in futures]

    def result(self, status: ResultStatus, **fields: Any) -> PipelineResult:
        return PipelineResult(status=status, language=self.language, trace=self.trace(), **fields)


async def run_pipeline(
    okr: OkrInput,
    provider: LLMProvider,
    *,
    max_retries: int = 2,
    on_progress: ProgressCallback | None = None,
    skip_clarification: bool = False,
    decomposed: dict[str, list[PlannedTask]] | None = None,
    budget: TimeBudget | None = None,
) -> PipelineResult:
    """Plan tasks for ``okr`` with ``provider``.

    Returns ``needs_clarification`` (no tasks) when the OKR is too vague, ``invalid_input``
    when deterministic checks fail, otherwise ``ok`` with validated tasks. Raises
    ``PipelineError`` with a structured ``failure`` when the provider is unreachable or its
    output stays invalid after ``max_retries`` retries.

    ``decomposed`` maps KR ids to tasks from an earlier run of the same OKR; those KRs skip
    the model. Every KR decomposed by this run is added to it, so after a failure it holds
    all finished KRs for a later resume.

    ``budget`` is the working time left in the quarter; decompose sizes each KR against it.
    """
    run = _Run(
        okr,
        provider,
        max_retries=max_retries,
        on_progress=on_progress,
        decomposed=decomposed,
        budget=budget,
    )
    return await run.run(skip_clarification=skip_clarification)
