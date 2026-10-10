"""In-process plan jobs (ADR 0001): pipeline → tasks → scheduler, with progress for SSE.

Database work runs in worker threads with short transactions; nothing holds a session while
the LLM is thinking. Progress lives in memory only; the durable outcome is the ``PlanRun`` row.
"""

import asyncio
import functools
import hashlib
import logging
import uuid
from collections import OrderedDict
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.api.schemas import (
    PlanEvent,
    PlanEventStatus,
    PlanEventType,
    PlanFailureCode,
    PlanRunStatus,
    PlanStage,
)
from app.calendar import working_days
from app.config import Settings
from app.persistence.models import (
    PlanRun,
    Quarter,
    Task,
    TaskDependency,
    utcnow,
)
from app.planner_llm import (
    ClarificationAnswer,
    KeyResultInput,
    LLMProvider,
    ObjectiveInput,
    OkrInput,
    PipelineError,
    PipelineResult,
    PlannedTask,
    ProgressEvent,
    RunTrace,
    TimeBudget,
    run_pipeline,
)
from app.planner_llm.schemas import Language
from app.scheduler import ScheduleInputError
from app.services.llm_settings import effective_settings
from app.services.scheduling import CalendarInputs, create_schedule_run, effective_today

logger = logging.getLogger(__name__)

ProviderResolver = Callable[[Settings], Awaitable[LLMProvider]]
Clock = Callable[[], date]

MAX_CLARIFY_ROUNDS = 2
ACTIVE_STATUSES = (PlanRunStatus.queued.value, PlanRunStatus.running.value)
RESUMABLE_STEPS = (PlanStage.decompose.value, PlanStage.dedup.value)
HEARTBEAT_SECONDS = 15.0
_STAGE_SPAN: dict[PlanStage, tuple[int, int]] = {
    PlanStage.precheck: (0, 5),
    PlanStage.clarify: (5, 20),
    PlanStage.decompose: (20, 80),
    PlanStage.dedup: (80, 90),
    PlanStage.validate: (90, 95),
    PlanStage.schedule: (95, 100),
}


def new_run_id() -> str:
    return str(uuid.uuid4())


def objective_key(objective_id: int) -> str:
    return f"o{objective_id}"


def kr_key(kr_id: int) -> str:
    return f"kr{kr_id}"


def parse_key(value: str | None, prefix: str) -> int | None:
    if not value or not value.startswith(prefix) or not value[len(prefix) :].isdigit():
        return None
    return int(value[len(prefix) :])


class EventLog:
    """Replayable progress of one job; late subscribers get every event from ``after``."""

    def __init__(self) -> None:
        self.events: list[PlanEvent] = []
        self.closed = False
        self._changed = asyncio.Condition()

    @property
    def last(self) -> PlanEvent | None:
        return self.events[-1] if self.events else None

    async def publish(self, event: PlanEvent) -> None:
        async with self._changed:
            self.events.append(event)
            self._changed.notify_all()

    async def close(self) -> None:
        async with self._changed:
            self.closed = True
            self._changed.notify_all()

    def _ready(self, seen: int) -> bool:
        return len(self.events) > seen or self.closed

    async def follow(
        self, after: int = 0, heartbeat: float = HEARTBEAT_SECONDS
    ) -> AsyncIterator[PlanEvent | None]:
        """Yield events with ``seq > after``; ``None`` is a keep-alive tick."""
        index = sum(1 for e in self.events if e.seq <= after)
        while True:
            async with self._changed:
                try:
                    await asyncio.wait_for(
                        self._changed.wait_for(functools.partial(self._ready, index)),
                        heartbeat,
                    )
                except TimeoutError:
                    batch: list[PlanEvent] | None = None
                else:
                    batch = self.events[index:]
                closed = self.closed
            if batch is None:
                yield None
                continue
            for event in batch:
                yield event
            index += len(batch)
            if closed and index >= len(self.events):
                return


class _Progress:
    """Turns pipeline events into ``PlanEvent`` with a monotonic overall percentage."""

    def __init__(self, log: EventLog) -> None:
        self.log = log
        self.percent = 0
        self.dedup_done = 0
        self.dedup_total = 0

    def _estimate(self, stage: PlanStage, event: ProgressEvent | None, status: str) -> int:
        low, high = _STAGE_SPAN[stage]
        if status in ("retry", "failed"):
            return self.percent
        if status == "skipped":
            return high
        if event is not None and event.total:
            if stage != PlanStage.dedup:
                return low + (high - low) * (event.completed or 0) // event.total
            self.dedup_total = event.total
        if stage == PlanStage.dedup and status == "completed" and self.dedup_total:
            self.dedup_done += 1
            return low + (high - low) * self.dedup_done // self.dedup_total
        return low if status == "started" else high

    async def emit(
        self,
        run_status: PlanRunStatus,
        stage: PlanStage | None,
        status: PlanEventStatus | None,
        event: ProgressEvent | None = None,
        *,
        end: bool = False,
    ) -> None:
        if end:
            if run_status == PlanRunStatus.succeeded:
                self.percent = 100
        elif stage is not None and status is not None:
            self.percent = max(self.percent, self._estimate(stage, event, status.value))
        await self.log.publish(
            PlanEvent(
                seq=len(self.log.events) + 1,
                type=PlanEventType.end if end else PlanEventType.progress,
                run_status=run_status,
                stage=stage,
                status=status,
                objective_id=parse_key(event.objective_id, "o") if event else None,
                key_result_id=parse_key(event.kr_id, "kr") if event else None,
                attempt=event.attempt if event else None,
                completed=event.completed if event else None,
                total=event.total if event else None,
                duration_ms=event.duration_ms if event else None,
                percent=self.percent,
            )
        )

    async def on_pipeline(self, event: ProgressEvent) -> None:
        await self.emit(
            PlanRunStatus.running, PlanStage(event.stage), PlanEventStatus(event.status), event
        )


@dataclass(frozen=True)
class _Prepared:
    okr: OkrInput
    settings: Settings
    skip_clarification: bool
    kr_ids: frozenset[int]
    decomposed: dict[str, list[PlannedTask]]
    budget: TimeBudget | None


def time_budget(session: Session, quarter: Quarter, today: date) -> TimeBudget | None:
    """Working time from ``today`` to the quarter end, as the scheduler will see it."""
    calendar = CalendarInputs(session, quarter)
    start = max(calendar.span.start, effective_today(quarter, today))
    days = working_days(start, calendar.span.end, calendar.config, calendar.holidays)
    if not days:
        return None
    minutes = sum(d.capacity_minutes for d in days)
    return TimeBudget(working_days=len(days), total_hours=round(minutes / 60, 1))


def build_okr(quarter: Quarter, run: PlanRun) -> tuple[OkrInput, frozenset[int]]:
    """The pipeline input for ``run``: active objectives and KRs plus the run's answers."""
    # An objective whose KRs were all dropped is left out like an inactive one.
    active = [
        o
        for o in quarter.objectives
        if o.active and (not o.key_results or any(kr.active for kr in o.key_results))
    ]
    objectives = [
        ObjectiveInput(
            id=objective_key(o.id),
            title=o.title,
            key_results=[
                KeyResultInput(
                    id=kr_key(kr.id),
                    text=kr.text,
                    unit=kr.unit,
                    baseline=kr.baseline,
                    target=kr.target,
                )
                for kr in o.key_results
                if kr.active
            ],
        )
        for o in active
    ]
    okr = OkrInput(
        objectives=objectives,
        context=run.context,
        language=cast("Language | None", run.language),
        clarifications=[
            ClarificationAnswer(
                question=c["question"],
                answer=c["answer"],
                kr_id=kr_key(c["key_result_id"]) if c.get("key_result_id") else None,
            )
            for c in run.clarifications
        ],
    )
    return okr, frozenset(kr.id for o in active for kr in o.key_results if kr.active)


def okr_fingerprint(okr: OkrInput) -> str:
    return hashlib.sha256(okr.model_dump_json().encode()).hexdigest()


def _dump_decomposed(decomposed: dict[str, list[PlannedTask]]) -> dict[str, Any]:
    return {kr: [t.model_dump() for t in tasks] for kr, tasks in decomposed.items()}


def _load_decomposed(stored: dict[str, Any] | None) -> dict[str, list[PlannedTask]]:
    return {
        kr: [PlannedTask.model_validate(t) for t in tasks] for kr, tasks in (stored or {}).items()
    }


def resume_blocker(session: Session, run: PlanRun) -> tuple[str, str] | None:
    """Why ``run`` cannot be resumed, as ``(code, message)``; ``None`` when it can.

    Only the latest run of a quarter that failed while decomposing or deduplicating, and
    whose OKR is unchanged since, can continue with the KRs it already decomposed.
    """
    step = (run.error or {}).get("step")
    if run.status != PlanRunStatus.failed.value or step not in RESUMABLE_STEPS:
        return "plan_not_resumable", f"plan {run.id} did not fail while decomposing"
    if run.decomposed is None or run.okr_hash is None:
        return "plan_not_resumable", f"plan {run.id} kept no decomposition to resume from"
    newer = session.scalar(
        select(PlanRun.id)
        .where(
            PlanRun.quarter_id == run.quarter_id,
            PlanRun.id != run.id,
            PlanRun.created_at > run.created_at,
        )
        .limit(1)
    )
    if newer is not None:
        return "plan_not_resumable", f"plan {run.id} was superseded by plan {newer}"
    okr, _ = build_okr(session.get_one(Quarter, run.quarter_id), run)
    if okr_fingerprint(okr) != run.okr_hash:
        return "okr_changed", f"the OKR changed after plan {run.id} failed; generate a new plan"
    return None


def _map_ids(item: dict[str, Any]) -> dict[str, Any]:
    """Pipeline ids (``o12``, ``kr5``) become database ids for the API."""
    mapped = {k: v for k, v in item.items() if k not in ("objective_id", "kr_id")}
    mapped["objective_id"] = parse_key(item.get("objective_id"), "o")
    mapped["key_result_id"] = parse_key(item.get("kr_id"), "kr")
    return mapped


def _apply_trace(run: PlanRun, trace: RunTrace) -> None:
    run.provider = trace.provider
    run.models = dict(trace.models)
    run.total_retries = trace.total_retries
    run.stage_duration_ms = dict(trace.stage_duration_ms)
    run.duration_ms = trace.duration_ms
    run.steps = [_map_ids(step.model_dump()) for step in trace.steps]


def failure_dict(
    code: PlanFailureCode,
    message: str,
    *,
    step: PlanStage | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code.value,
        "step": step.value if step else None,
        "message": message,
        "provider": provider,
        "model": None,
        "objective_id": None,
        "key_result_id": None,
        "attempts": 0,
        "errors": [],
        "suggestions": [],
    }


class PlanJobManager:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        provider_resolver: ProviderResolver,
        today: Clock,
        *,
        max_logs: int = 50,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.provider_resolver = provider_resolver
        self.today = today
        self.max_logs = max_logs
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._logs: OrderedDict[str, EventLog] = OrderedDict()

    def log(self, run_id: str) -> EventLog | None:
        return self._logs.get(run_id)

    def is_active(self, run_id: str) -> bool:
        return run_id in self._tasks

    def start(self, run_id: str) -> None:
        """Must be called from the event loop that serves the SSE streams."""
        log = EventLog()
        self._logs[run_id] = log
        while len(self._logs) > self.max_logs:
            oldest = next(iter(self._logs))
            if oldest in self._tasks:
                break
            self._logs.pop(oldest)
        task = asyncio.create_task(self._run(run_id, log), name=f"plan-run-{run_id}")
        self._tasks[run_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run_id, None))

    async def cancel(self, run_id: str) -> bool:
        task = self._tasks.get(run_id)
        if task is None:
            return False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return True

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def mark_interrupted(self) -> int:
        """Runs left queued/running by a previous process can never finish."""
        with self.session_factory() as session:
            result = session.execute(
                update(PlanRun)
                .where(PlanRun.status.in_(ACTIVE_STATUSES))
                .values(
                    status=PlanRunStatus.failed.value,
                    finished_at=utcnow(),
                    error=failure_dict(
                        PlanFailureCode.interrupted, "the server restarted while the plan ran"
                    ),
                )
            )
            session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    async def _run(self, run_id: str, log: EventLog) -> None:
        progress = _Progress(log)
        final = PlanRunStatus.failed
        try:
            final = await self._execute(run_id, progress)
        except asyncio.CancelledError:
            final = PlanRunStatus.cancelled
            await asyncio.to_thread(self._finish, run_id, final, None, None)
            raise
        except Exception:
            logger.exception("plan run crashed run_id=%s", run_id)
            await asyncio.to_thread(
                self._finish,
                run_id,
                final,
                None,
                failure_dict(PlanFailureCode.internal_error, "unexpected server error"),
            )
        finally:
            await progress.emit(final, None, None, end=True)
            await log.close()

    async def _execute(self, run_id: str, progress: _Progress) -> PlanRunStatus:
        prepared = await asyncio.to_thread(self._prepare, run_id)
        await progress.emit(PlanRunStatus.running, None, None)
        provider = await self.provider_resolver(prepared.settings)
        logger.info("plan run started run_id=%s provider=%s", run_id, provider.name)
        try:
            result = await run_pipeline(
                prepared.okr,
                provider,
                max_retries=prepared.settings.llm_max_json_retries,
                on_progress=progress.on_pipeline,
                skip_clarification=prepared.skip_clarification,
                decomposed=prepared.decomposed,
                budget=prepared.budget,
            )
        except PipelineError as exc:
            failure = _map_ids(exc.failure.model_dump())
            await asyncio.to_thread(
                self._finish,
                run_id,
                PlanRunStatus.failed,
                exc.trace,
                failure,
                prepared.decomposed,
            )
            return PlanRunStatus.failed

        if result.status == "needs_clarification":
            await asyncio.to_thread(self._save_questions, run_id, result)
            return PlanRunStatus.needs_clarification
        if result.status == "invalid_input":
            await asyncio.to_thread(self._save_issues, run_id, result)
            return PlanRunStatus.invalid_input

        await progress.emit(PlanRunStatus.running, PlanStage.schedule, PlanEventStatus.started)
        try:
            await asyncio.to_thread(self._save_plan, run_id, result, prepared)
        except ScheduleInputError as exc:
            failure = failure_dict(
                PlanFailureCode.schedule_input_error, str(exc), step=PlanStage.schedule
            )
            await asyncio.to_thread(
                self._finish, run_id, PlanRunStatus.failed, result.trace, failure
            )
            return PlanRunStatus.failed
        await progress.emit(PlanRunStatus.running, PlanStage.schedule, PlanEventStatus.completed)
        return PlanRunStatus.succeeded

    def _prepare(self, run_id: str) -> _Prepared:
        with self.session_factory() as session:
            run = session.get_one(PlanRun, run_id)
            quarter = session.get_one(Quarter, run.quarter_id)
            run.status = PlanRunStatus.running.value
            run.started_at = utcnow()
            okr, kr_ids = build_okr(quarter, run)
            run.okr_hash = okr_fingerprint(okr)
            decomposed: dict[str, list[PlannedTask]] = {}
            parent = session.get(PlanRun, run.parent_id) if run.parent_id else None
            # The OKR may change between the resume request and this point; then start over.
            if (
                parent is not None
                and parent.status == PlanRunStatus.failed.value
                and parent.okr_hash == run.okr_hash
            ):
                decomposed = _load_decomposed(parent.decomposed)
            prepared = _Prepared(
                okr=okr,
                settings=effective_settings(session, self.settings),
                skip_clarification=run.skip_clarification,
                kr_ids=kr_ids,
                decomposed=decomposed,
                budget=time_budget(session, quarter, self.today()),
            )
            session.commit()
            return prepared

    def _finish(
        self,
        run_id: str,
        status: PlanRunStatus,
        trace: RunTrace | None,
        error: dict[str, Any] | None,
        decomposed: dict[str, list[PlannedTask]] | None = None,
    ) -> None:
        with self.session_factory() as session:
            run = session.get(PlanRun, run_id)
            if run is None:
                return
            if trace is not None:
                _apply_trace(run, trace)
            if decomposed is not None:
                run.decomposed = _dump_decomposed(decomposed)
            run.status = status.value
            run.error = error
            run.finished_at = utcnow()
            session.commit()

    def _save_questions(self, run_id: str, result: PipelineResult) -> None:
        with self.session_factory() as session:
            run = session.get_one(PlanRun, run_id)
            _apply_trace(run, result.trace)
            run.language = result.language
            run.questions = [_map_ids(q.model_dump()) for q in result.questions]
            run.status = PlanRunStatus.needs_clarification.value
            run.finished_at = utcnow()
            session.commit()

    def _save_issues(self, run_id: str, result: PipelineResult) -> None:
        with self.session_factory() as session:
            run = session.get_one(PlanRun, run_id)
            _apply_trace(run, result.trace)
            run.language = result.language
            run.issues = [_map_ids(i.model_dump()) for i in result.issues]
            run.status = PlanRunStatus.invalid_input.value
            run.finished_at = utcnow()
            session.commit()

    def _save_plan(self, run_id: str, result: PipelineResult, prepared: _Prepared) -> None:
        """Replace the quarter's regenerable tasks and schedule them, in one transaction.

        Finished, pinned and user-edited tasks are kept, and so are the tasks of paused
        objectives; they are the user's decisions, not the model's.
        """
        with self.session_factory() as session, session.begin():
            run = session.get_one(PlanRun, run_id)
            quarter = session.get_one(Quarter, run.quarter_id)
            replaceable = select(Task.id).where(
                Task.key_result_id.in_(prepared.kr_ids),
                Task.status != "done",
                Task.pinned.is_(False),
                Task.user_edited.is_(False),
            )
            session.execute(
                delete(Task)
                .where(Task.id.in_(replaceable))
                .execution_options(synchronize_session=False)
            )

            created: dict[str, Task] = {}
            kept = session.execute(
                select(Task.key_result_id, func.max(Task.position))
                .where(Task.key_result_id.in_(prepared.kr_ids))
                .group_by(Task.key_result_id)
            ).all()
            positions: dict[int, int] = {kr_id: int(top) + 1 for kr_id, top in kept}
            for planned in result.tasks:
                kr_id = parse_key(planned.kr_id, "kr")
                if kr_id is None or kr_id not in prepared.kr_ids:
                    raise ScheduleInputError(
                        "unknown_dependency", (planned.local_id,), "task has an unknown key result"
                    )
                position = positions.get(kr_id, 0)
                positions[kr_id] = position + 1
                created[planned.local_id] = Task(
                    key_result_id=kr_id,
                    plan_run_id=run_id,
                    source_key=planned.local_id[:100],
                    title=planned.title.strip()[:300],
                    description=planned.description.strip(),
                    done_criteria=planned.done_criteria.strip(),
                    estimate_minutes=max(1, round(planned.estimate_hours * 60)),
                    position=position,
                )
            session.add_all(created.values())
            session.flush()
            session.add_all(
                TaskDependency(task_id=created[p.local_id].id, depends_on_id=created[dep].id)
                for p in result.tasks
                for dep in p.depends_on
            )
            session.flush()
            session.expire_all()

            create_schedule_run(session, quarter, self.today(), plan_run_id=run_id)
            run = session.get_one(PlanRun, run_id)
            _apply_trace(run, result.trace)
            run.language = result.language
            run.task_count = len(created)
            run.status = PlanRunStatus.succeeded.value
            run.finished_at = utcnow()
