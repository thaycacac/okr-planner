import json
import logging
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from app.planner_llm import (
    ClarificationAnswer,
    KeyResultInput,
    ObjectiveInput,
    OkrInput,
    PipelineError,
    ProgressEvent,
    TimeBudget,
    run_pipeline,
)
from app.planner_llm.providers.base import Prompt, strict_json_schema
from app.planner_llm.providers.errors import (
    InvalidJSONError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.planner_llm.providers.fake import FakeProvider, FakeReply
from app.planner_llm.providers.local import LocalProvider
from app.planner_llm.schemas import KeyResultCheck, KeyResultNeedsOutput, LinkOutput

KR_TEXTS = {
    "kr1": "Launch the new onboarding flow for web users",
    "kr2": "Publish the help center with setup guides",
}


def _okr(**overrides: Any) -> OkrInput:
    data: dict[str, Any] = {
        "objectives": [
            ObjectiveInput(
                id="o1",
                title="Deliver a smooth first-week experience",
                key_results=[KeyResultInput(id=k, text=t) for k, t in KR_TEXTS.items()],
            )
        ]
    }
    data.update(overrides)
    return OkrInput(**data)


def _task(
    local_id: str, kr_id: str, hours: float = 4, deps: list[str] | None = None
) -> dict[str, Any]:
    return {
        "local_id": local_id,
        "title": f"Task {local_id}",
        "description": "Do the work",
        "estimate_hours": hours,
        "done_criteria": "Reviewed and merged",
        "depends_on": deps or [],
        "kr_id": kr_id,
    }


def _decompose_ok(kr_id: str) -> dict[str, Any]:
    return {"tasks": [_task("t1", kr_id), _task("t2", kr_id, 3, ["t1"])]}


CLARIFY_OK = {"status": "ok", "questions": []}
CHECK_CLEAR = {"end_result": "done", "concrete": True}
CHECK_VAGUE = {"end_result": "", "concrete": False}
DEDUP_NOOP = {"merges": [], "cross_dependencies": []}
NEEDS_NONE: dict[str, Any] = {"needs": []}
LINK_NONE: dict[str, Any] = {"links": []}


class Script:
    """Per-step replies; a list is consumed in order and its last item repeats.

    ``check`` / ``check:<kr_id>`` answer the per-KR clarity check, which defaults to clear;
    ``needs`` and ``link`` answer the pass that links key results, which defaults to no links.
    """

    def __init__(self, **replies: Any) -> None:
        self.replies = replies

    def __call__(self, prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if schema is KeyResultCheck:
            reply = self.replies.get(f"check:{prompt.kr_id}", self.replies.get("check"))
            reply = CHECK_CLEAR if reply is None else reply
        elif schema is KeyResultNeedsOutput:
            reply = self.replies.get("needs", NEEDS_NONE)
        elif schema is LinkOutput:
            reply = self.replies.get("link", LINK_NONE)
        else:
            key = f"{prompt.step}:{prompt.kr_id}" if prompt.kr_id else prompt.step
            reply = self.replies.get(key, self.replies.get(prompt.step))
        if reply is None and prompt.step == "decompose":
            assert prompt.kr_id is not None
            return _decompose_ok(prompt.kr_id)
        if reply is None:
            return {"clarify": CLARIFY_OK, "dedup": DEDUP_NOOP}[prompt.step]
        if isinstance(reply, list):
            return reply.pop(0) if len(reply) > 1 else reply[0]
        assert isinstance(reply, dict | Exception)
        return reply


def _calls(provider: FakeProvider, step: str, kr_id: str | None = None) -> list[Prompt]:
    return [c for c in provider.calls if c.step == step and (kr_id is None or c.kr_id == kr_id)]


def _checks(provider: FakeProvider) -> list[Prompt]:
    return [c for c in _calls(provider, "clarify") if c.kr_id is not None]


def _asks(provider: FakeProvider) -> list[Prompt]:
    return [c for c in _calls(provider, "clarify") if c.kr_id is None]


def _reviews(provider: FakeProvider) -> list[Prompt]:
    """The plan-wide dedup calls, without the pass that links key results."""
    return [c for c in _calls(provider, "dedup") if c.system.startswith("You review a quarter")]


async def test_clear_okr_produces_tasks_for_every_kr() -> None:
    provider = FakeProvider(Script())

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert result.language == "en"
    assert result.questions == []
    assert {t.kr_id for t in result.tasks} == {"kr1", "kr2"}
    assert [t.local_id for t in result.tasks] == ["kr1.t1", "kr1.t2", "kr2.t1", "kr2.t2"]
    assert result.tasks[1].depends_on == ["kr1.t1"]
    assert all(t.objective_id == "o1" for t in result.tasks)
    assert all(2 <= t.estimate_hours <= 6 for t in result.tasks)

    trace = result.trace
    assert trace.provider == "local"
    assert trace.models == {
        "clarify": "fake-model:clarify",
        "decompose": "fake-model:decompose",
        "dedup": "fake-model:dedup",
    }
    assert trace.total_retries == 0
    assert [s.step for s in trace.steps] == [
        "precheck",
        "clarify",
        "clarify",
        "decompose",
        "decompose",
        "dedup",
        "dedup",
        "validate",
    ]
    assert set(trace.stage_duration_ms) == {"precheck", "clarify", "decompose", "dedup", "validate"}
    assert [c.kr_id for c in _checks(provider)] == ["kr1", "kr2"]
    assert _asks(provider) == []


async def test_vague_okr_needs_clarification_and_creates_no_tasks() -> None:
    questions = [
        {"kr_id": f"kr{i % 2 + 1}", "question": f"Question {i}?", "reason": "vague"}
        for i in range(7)
    ]
    provider = FakeProvider(
        Script(
            check=CHECK_VAGUE,
            clarify={"status": "needs_clarification", "questions": questions},
        )
    )

    result = await run_pipeline(_okr(), provider)

    assert result.status == "needs_clarification"
    assert result.tasks == []
    assert len(result.questions) == 5
    assert [q.id for q in result.questions] == ["q1", "q2", "q3", "q4", "q5"]
    assert all(q.source == "llm" for q in result.questions)
    assert _calls(provider, "decompose") == []
    assert _calls(provider, "dedup") == []


async def test_metric_without_baseline_is_asked_before_llm_questions() -> None:
    okr = OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Tăng trưởng doanh thu quý này",
                key_results=[KeyResultInput(id="kr1", text="Tăng doanh thu từ khách hàng mới")],
            )
        ]
    )
    provider = FakeProvider(Script())

    result = await run_pipeline(okr, provider)

    assert result.status == "needs_clarification"
    assert result.language == "vi"
    assert result.questions[0].source == "precheck"
    assert result.questions[0].kr_id == "kr1"
    assert "baseline" in result.questions[0].question
    assert _calls(provider, "clarify") == []


async def test_answered_metric_question_lets_planning_continue() -> None:
    okr = OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Tăng trưởng doanh thu quý này",
                key_results=[KeyResultInput(id="kr1", text="Tăng doanh thu từ khách hàng mới")],
            )
        ],
        clarifications=[
            ClarificationAnswer(
                kr_id="kr1", question="Baseline?", answer="Hiện 100 triệu, mục tiêu 150 triệu"
            )
        ],
    )
    provider = FakeProvider(Script())

    result = await run_pipeline(okr, provider)

    assert result.status == "ok"
    decompose_prompt = _calls(provider, "decompose", "kr1")[0]
    assert "Vietnamese" in decompose_prompt.system
    assert json.loads(decompose_prompt.user)["clarifications"][0]["answer"].startswith("Hiện")


async def test_skip_clarification_goes_straight_to_decompose() -> None:
    provider = FakeProvider(
        Script(check=CHECK_VAGUE, clarify={"status": "needs_clarification", "questions": []})
    )

    result = await run_pipeline(_okr(), provider, skip_clarification=True)

    assert result.status == "ok"
    assert _calls(provider, "clarify") == []


async def test_invalid_input_stops_before_any_llm_call() -> None:
    okr = OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Ship",
                key_results=[
                    KeyResultInput(id="kr1", text="Publish the help center"),
                    KeyResultInput(id="kr2", text="publish the  help center!"),
                ],
            )
        ]
    )
    provider = FakeProvider(Script())

    result = await run_pipeline(okr, provider)

    assert result.status == "invalid_input"
    assert {i.code for i in result.issues} == {"objective_too_short", "duplicate_kr"}
    assert provider.calls == []


async def test_invalid_json_retries_exactly_max_retries_then_fails() -> None:
    provider = FakeProvider(Script(**{"decompose:kr2": InvalidJSONError("invalid JSON at line 1")}))

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider)

    failure = caught.value.failure
    assert failure.code == "invalid_llm_output"
    assert failure.step == "decompose"
    assert failure.kr_id == "kr2"
    assert failure.attempts == 3
    assert failure.provider == "local"
    assert "switch_provider" in failure.suggestions
    assert len(_calls(provider, "decompose", "kr2")) == 3
    assert [c.attempt for c in _calls(provider, "decompose", "kr2")] == [0, 1, 2]
    kr2_trace = next(
        s for s in caught.value.trace.steps if s.step == "decompose" and s.kr_id == "kr2"
    )
    assert kr2_trace.retries == 2


async def test_max_retries_is_configurable() -> None:
    provider = FakeProvider(Script(check=CHECK_VAGUE, clarify={"status": "maybe", "questions": []}))

    with pytest.raises(PipelineError):
        await run_pipeline(_okr(), provider, max_retries=0)

    assert len(_asks(provider)) == 1


async def test_schema_error_is_retried_with_specific_feedback() -> None:
    bad = {"tasks": [{"local_id": "t1", "title": "x"}]}
    provider = FakeProvider(Script(**{"decompose:kr1": [bad, _decompose_ok("kr1")]}))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert result.trace.total_retries == 1
    retry = _calls(provider, "decompose", "kr1")[1]
    assert "previous answer was rejected" in retry.user
    assert "tasks.0.estimate_hours: Field required" in retry.user


async def test_task_over_six_hours_must_be_split() -> None:
    too_big = {"tasks": [_task("t1", "kr1", hours=10)]}
    provider = FakeProvider(Script(**{"decompose:kr1": [too_big, _decompose_ok("kr1")]}))

    result = await run_pipeline(_okr(), provider)

    retry = _calls(provider, "decompose", "kr1")[1]
    assert "estimate_hours 10 is above 6; split it" in retry.user
    assert all(t.estimate_hours <= 6 for t in result.tasks)


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ({"tasks": [_task("t1", "kr9")]}, "kr_id 'kr9' is not valid"),
        ({"tasks": [_task("t1", "kr1", deps=["t2"]), _task("t2", "kr1", deps=["t1"])]}, "cycle"),
        ({"tasks": [_task("t1", "kr1", deps=["t7"])]}, "depends_on 't7' is not a local_id"),
        ({"tasks": []}, "return at least one task"),
        ({"tasks": [_task("t1", "kr1", hours=1)]}, "below 2"),
    ],
)
async def test_rule_violations_are_retried(reply: dict[str, Any], expected: str) -> None:
    provider = FakeProvider(Script(**{"decompose:kr1": [reply, _decompose_ok("kr1")]}))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert expected in _calls(provider, "decompose", "kr1")[1].user
    assert {t.kr_id for t in result.tasks} == {"kr1", "kr2"}


async def test_dedup_merges_duplicates_and_adds_cross_kr_dependency() -> None:
    dedup = {
        "merges": [{"keep_id": "kr1.t2", "remove_ids": ["kr2.t1"], "reason": "same work"}],
        "cross_dependencies": [
            {"task_id": "kr2.t2", "depends_on_id": "kr1.t1", "reason": "needs flow"}
        ],
    }
    provider = FakeProvider(Script(dedup=dedup))

    result = await run_pipeline(_okr(), provider)

    by_id = {t.local_id: t for t in result.tasks}
    assert "kr2.t1" not in by_id
    assert by_id["kr2.t2"].depends_on == ["kr1.t2", "kr1.t1"]
    assert {t.kr_id for t in result.tasks} == {"kr1", "kr2"}


async def test_dedup_that_empties_a_kr_is_rejected_and_retried() -> None:
    wipe_kr2 = {
        "merges": [{"keep_id": "kr1.t1", "remove_ids": ["kr2.t1"], "reason": "dup"}],
        "cross_dependencies": [],
    }
    single_task_kr2 = {"tasks": [_task("t1", "kr2")]}
    provider = FakeProvider(
        Script(dedup=[wipe_kr2, DEDUP_NOOP], **{"decompose:kr2": single_task_kr2})
    )

    result = await run_pipeline(_okr(), provider)

    assert len(_reviews(provider)) == 2
    assert "keep at least one task per key result" in _reviews(provider)[1].user
    assert {t.kr_id for t in result.tasks} == {"kr1", "kr2"}


async def test_dedup_rejects_merging_consecutive_steps() -> None:
    consecutive = {
        "merges": [{"keep_id": "kr1.t2", "remove_ids": ["kr1.t1", "kr2.t1"]}],
        "cross_dependencies": [],
    }
    provider = FakeProvider(Script(dedup=[consecutive, DEDUP_NOOP]))

    result = await run_pipeline(_okr(), provider)

    retry = _reviews(provider)[1].user
    assert "kr1.t2 depends on kr1.t1, so they are consecutive steps" in retry
    assert len(result.tasks) == 4


async def test_dedup_merges_inside_one_key_result_are_dropped() -> None:
    inside = {"merges": [{"keep_id": "kr1.t2", "remove_ids": ["kr1.t1"]}], "cross_dependencies": []}
    provider = FakeProvider(Script(dedup=inside))

    result = await run_pipeline(_okr(), provider)

    assert result.trace.total_retries == 0
    assert [t.local_id for t in result.tasks] == ["kr1.t1", "kr1.t2", "kr2.t1", "kr2.t2"]


async def test_blank_dependencies_are_ignored_without_retry() -> None:
    reply = {"tasks": [_task("t1", "kr1", deps=[""]), _task("t2", "kr1", deps=[" t1 "])]}
    provider = FakeProvider(Script(**{"decompose:kr1": reply}))

    result = await run_pipeline(_okr(), provider)

    assert result.trace.total_retries == 0
    assert [t.depends_on for t in result.tasks if t.kr_id == "kr1"] == [[], ["kr1.t1"]]


async def test_only_key_results_not_asked_by_precheck_are_checked() -> None:
    okr = OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Làm cho sản phẩm tốt hơn",
                key_results=[
                    KeyResultInput(id="kr1", text="Cải thiện trải nghiệm người dùng"),
                    KeyResultInput(id="kr2", text="Học thêm nhiều kỹ năng mới"),
                ],
            )
        ]
    )
    rephrased = {
        "kr_id": "kr1",
        "question": "Chỉ số nào được sử dụng để đo cải thiện trải nghiệm người dùng?",
        "reason": "thiếu số đo",
    }
    other = {"kr_id": "kr2", "question": "Kỹ năng cụ thể nào cần học?", "reason": "mơ hồ"}
    ask = [
        {"status": "needs_clarification", "questions": [rephrased, other]},
        {"status": "needs_clarification", "questions": [other]},
    ]
    provider = FakeProvider(Script(check=CHECK_VAGUE, clarify=ask))

    result = await run_pipeline(okr, provider)

    assert [c.kr_id for c in _checks(provider)] == ["kr2"]
    assert json.loads(_asks(provider)[0].user)["vague_key_results"] == [
        {"id": "kr2", "text": "Học thêm nhiều kỹ năng mới"}
    ]
    assert "kr_id 'kr1' is unknown" in _asks(provider)[1].user
    assert [(q.source, q.kr_id) for q in result.questions] == [("precheck", "kr1"), ("llm", "kr2")]
    assert "Vietnamese" in _asks(provider)[0].system


async def test_dedup_cycle_is_rejected() -> None:
    cyclic = {
        "merges": [],
        "cross_dependencies": [
            {"task_id": "kr1.t1", "depends_on_id": "kr2.t2", "reason": "a"},
            {"task_id": "kr2.t1", "depends_on_id": "kr1.t2", "reason": "b"},
        ],
    }
    provider = FakeProvider(Script(dedup=[cyclic, DEDUP_NOOP]))

    await run_pipeline(_okr(), provider)

    assert "cycle" in _reviews(provider)[1].user


async def test_dedup_is_skipped_for_single_kr_objectives() -> None:
    okr = _okr(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Deliver a smooth first-week experience",
                key_results=[KeyResultInput(id="kr1", text=KR_TEXTS["kr1"])],
            )
        ]
    )
    provider = FakeProvider(Script())

    result = await run_pipeline(okr, provider)

    assert result.status == "ok"
    assert _calls(provider, "dedup") == []


def _two_objectives() -> OkrInput:
    return _okr(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Ship the new release",
                key_results=[KeyResultInput(id="kr1", text=KR_TEXTS["kr1"])],
            ),
            ObjectiveInput(
                id="o2",
                title="Grow active users",
                key_results=[KeyResultInput(id="kr2", text="Run the launch campaign")],
            ),
        ]
    )


async def test_dedup_sees_the_whole_plan_and_links_objectives() -> None:
    dedup = {
        "merges": [],
        "cross_dependencies": [
            {"task_id": "kr2.t1", "depends_on_id": "kr1.t2", "reason": "needs the release"}
        ],
    }
    provider = FakeProvider(Script(dedup=dedup))

    result = await run_pipeline(_two_objectives(), provider)

    [call] = _reviews(provider)
    payload = json.loads(call.user)
    assert call.objective_id is None
    assert {t["id"] for t in payload["tasks"]} == {"kr1.t1", "kr1.t2", "kr2.t1", "kr2.t2"}
    assert payload["key_results"][1] == {
        "id": "kr2",
        "objective_id": "o2",
        "text": "Run the launch campaign",
    }
    assert payload["tasks"][0] == {"id": "kr1.t1", "kr_id": "kr1", "title": "Task t1"}
    assert "objectives" not in payload
    by_id = {t.local_id: t for t in result.tasks}
    assert by_id["kr2.t1"].depends_on == ["kr1.t2"]
    assert by_id["kr2.t1"].objective_id == "o2"


RELEASE_NEED = {"kr_id": "kr2", "needs_kr_id": "kr1", "output": "the finished release"}


def _links(provider: FakeProvider) -> list[Prompt]:
    return [c for c in _calls(provider, "dedup") if c.system.startswith("Key result kr2 needs")]


async def test_a_need_between_key_results_is_linked_task_to_task() -> None:
    link = {"task_id": "kr2.t2", "depends_on_id": "kr1.t2", "reason": "needs the release"}
    provider = FakeProvider(Script(needs={"needs": [RELEASE_NEED]}, link={"links": [link]}))

    result = await run_pipeline(_two_objectives(), provider)

    by_id = {t.local_id: t for t in result.tasks}
    assert by_id["kr2.t1"].depends_on == []
    assert by_id["kr2.t2"].depends_on == ["kr2.t1", "kr1.t2"]
    needs_call = next(c for c in _calls(provider, "dedup") if "find the order" in c.system)
    assert json.loads(needs_call.user)["key_results"][1] == {
        "id": "kr2",
        "objective": "Grow active users",
        "text": "Run the launch campaign",
    }
    (link_call,) = _links(provider)
    payload = json.loads(link_call.user)
    assert [t["id"] for t in payload["needing_tasks"]] == ["kr2.t1", "kr2.t2"]
    assert payload["giving_tasks"] == [
        {"id": "kr1.t1", "title": "Task t1"},
        {"id": "kr1.t2", "title": "Task t2"},
    ]


async def test_a_need_the_review_already_linked_gets_no_link_call() -> None:
    dedup = {
        "merges": [],
        "cross_dependencies": [{"task_id": "kr2.t1", "depends_on_id": "kr1.t2", "reason": "x"}],
    }
    provider = FakeProvider(Script(dedup=dedup, needs={"needs": [RELEASE_NEED]}))

    await run_pipeline(_two_objectives(), provider)

    assert _links(provider) == []


async def test_bad_needs_and_links_add_nothing_instead_of_failing_the_plan() -> None:
    self_need = {"kr_id": "kr2", "needs_kr_id": "kr2", "output": "itself"}
    backwards = {"task_id": "kr1.t1", "depends_on_id": "kr2.t2", "reason": "wrong way"}
    provider = FakeProvider(
        Script(needs={"needs": [self_need, RELEASE_NEED]}, link={"links": [backwards]})
    )

    result = await run_pipeline(_two_objectives(), provider)

    assert result.status == "ok"
    assert all(dep.split(".")[0] == t.kr_id for t in result.tasks for dep in t.depends_on)
    assert len(_links(provider)) == 3
    assert "task_id 'kr1.t1' is not one of needing_tasks" in _links(provider)[1].user


async def test_decompose_prompt_carries_the_quarter_time_budget() -> None:
    provider = FakeProvider(Script())
    budget = TimeBudget(working_days=66, total_hours=132)

    await run_pipeline(_two_objectives(), provider, budget=budget)

    system = _calls(provider, "decompose", "kr1")[0].system
    assert "66 working days left in the quarter at about 2 hours per day" in system
    assert "132 hours in total, 118.8 hours usable after the schedule buffer" in system
    assert "All 2 key results of the plan share this budget, about 59 hours each" in system
    assert "This key result must stay within 89 hours." in system
    assert "aiming for" not in system
    assert "Never number tasks as parts" in system
    assert "not the title restated" in system
    other = json.loads(_calls(provider, "decompose", "kr1")[0].user)["other_key_results"]
    assert other == [{"id": "kr2", "text": "Run the launch campaign"}]


async def test_decompose_prompt_without_budget_still_asks_for_the_life_cycle() -> None:
    provider = FakeProvider(Script())

    await run_pipeline(_okr(), provider)

    system = _calls(provider, "decompose", "kr1")[0].system
    assert "Time budget" not in system
    assert "measure the baseline before any improvement" in system
    assert "independent batches of repeated work do not depend on each other" in system


def _named(local_id: str, kr_id: str, title: str, done: str, hours: float = 4) -> dict[str, Any]:
    return {**_task(local_id, kr_id, hours), "title": title, "done_criteria": done}


PADDED = {
    "tasks": [
        _named("t1", "kr1", "Implement onboarding improvements part 1", "Improvements implemented"),
        _named("t2", "kr1", "Implement onboarding improvements part 2", "Improvements finalized"),
    ]
}


async def test_padding_tasks_are_retried_with_quality_feedback() -> None:
    provider = FakeProvider(Script(**{"decompose:kr1": [PADDED, _decompose_ok("kr1")]}))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    retry = _calls(provider, "decompose", "kr1")[1].user
    assert "task t1: title is numbered as a part" in retry
    assert "task t2: done_criteria only repeats the title" in retry
    assert [t.title for t in result.tasks if t.kr_id == "kr1"] == ["Task t1", "Task t2"]


async def test_quality_rules_keep_the_last_plan_once_retries_run_out() -> None:
    provider = FakeProvider(Script(**{"decompose:kr1": PADDED}))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert len(_calls(provider, "decompose", "kr1")) == 3
    assert [t.local_id for t in result.tasks if t.kr_id == "kr1"] == ["kr1.t1", "kr1.t2"]
    (kr1_step,) = [s for s in result.trace.steps if s.step == "decompose" and s.kr_id == "kr1"]
    assert kr1_step.retries == 2
    assert any("title is numbered as a part" in e for e in kr1_step.errors)


async def test_structural_errors_still_fail_once_retries_run_out() -> None:
    padded_and_too_long = {
        "tasks": [_named("t1", "kr1", "Implement it part 1", "Implemented", hours=12)]
    }
    provider = FakeProvider(Script(**{"decompose:kr1": padded_and_too_long}))

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider)

    assert caught.value.failure.code == "invalid_llm_output"
    assert caught.value.failure.kr_id == "kr1"


SMALL_BUDGET = TimeBudget(working_days=10, total_hours=15)


def _hours_plan(kr_id: str, *hours: float) -> dict[str, Any]:
    return {"tasks": [_task(f"t{i}", kr_id, h) for i, h in enumerate(hours, start=1)]}


async def test_key_result_over_its_share_of_the_budget_is_retried() -> None:
    provider = FakeProvider(
        Script(
            **{
                "decompose:kr1": [_hours_plan("kr1", 4, 4, 4), _hours_plan("kr1", 4, 3)],
                "decompose:kr2": _hours_plan("kr2", 2, 2),
            }
        )
    )

    result = await run_pipeline(_okr(), provider, budget=SMALL_BUDGET)

    first, retry = _calls(provider, "decompose", "kr1")
    assert "This key result must stay within 10 hours." in first.system
    assert "estimates add up to 12 hours, above the 10 hours this key result may use" in retry.user
    assert sum(t.estimate_hours for t in result.tasks) == 11


async def test_plan_over_the_quarter_budget_replans_only_heavy_key_results() -> None:
    provider = FakeProvider(
        Script(
            **{
                "decompose:kr1": [_hours_plan("kr1", 4, 4), _hours_plan("kr1", 4, 3)],
                "decompose:kr2": _hours_plan("kr2", 3, 3),
            }
        )
    )
    events: list[ProgressEvent] = []

    result = await run_pipeline(_okr(), provider, budget=SMALL_BUDGET, on_progress=events.append)

    first, replan = _calls(provider, "decompose", "kr1")
    assert "must stay within 10 hours" in first.system
    assert "must stay within 7 hours" in replan.system
    assert replan.attempt == 0
    assert len(_calls(provider, "decompose", "kr2")) == 1
    assert sum(t.estimate_hours for t in result.tasks) == 13 <= SMALL_BUDGET.usable_hours
    assert [t.local_id for t in result.tasks] == ["kr1.t1", "kr1.t2", "kr2.t1", "kr2.t2"]
    done = [e for e in events if e.stage == "decompose" and e.status == "completed" and e.kr_id]
    assert len(done) == 3
    assert (done[-1].kr_id, done[-1].completed, done[-1].total) == ("kr1", 2, 2)


async def test_measurable_key_results_skip_the_clarity_check() -> None:
    okr = _okr(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Deliver a smooth first-week experience",
                key_results=[
                    KeyResultInput(
                        id="kr1",
                        text="Raise activation from 20% to 35%",
                        metric="activation rate",
                        baseline=20,
                        target=35,
                    ),
                    KeyResultInput(id="kr2", text=KR_TEXTS["kr2"]),
                ],
            )
        ]
    )
    provider = FakeProvider(Script())

    result = await run_pipeline(okr, provider)

    assert result.status == "ok"
    assert [c.kr_id for c in _checks(provider)] == ["kr2"]


async def test_clarify_prompts_leave_execution_details_to_planning() -> None:
    question = {"kr_id": "kr2", "question": "Which guides count?", "reason": "vague"}
    provider = FakeProvider(
        Script(
            **{"check:kr2": CHECK_VAGUE},
            clarify={"status": "needs_clarification", "questions": [question]},
        )
    )

    await run_pipeline(_okr(), provider)

    assert "planning decides them" in _checks(provider)[0].system
    (ask,) = _asks(provider)
    assert "Never ask how to do the work" in ask.system
    assert "Never ask about the other key results" in ask.system


async def test_dedup_answers_beyond_the_limits_are_ignored() -> None:
    link = {"task_id": "kr2.t1", "depends_on_id": "kr1.t2"}
    unknown = {"task_id": "kr9.t1", "depends_on_id": "kr1.t1"}
    dedup = {"merges": [], "cross_dependencies": [link] * 8 + [unknown]}
    provider = FakeProvider(Script(dedup=dedup))

    result = await run_pipeline(_okr(), provider)

    assert result.trace.total_retries == 0
    assert len(_reviews(provider)) == 1
    assert {t.local_id: t for t in result.tasks}["kr2.t1"].depends_on == ["kr1.t2"]
    assert "At most 5 merges" in _reviews(provider)[0].system


async def test_dedup_links_inside_one_key_result_are_dropped() -> None:
    backwards = {"task_id": "kr1.t1", "depends_on_id": "kr1.t2"}
    link = {"task_id": "kr2.t1", "depends_on_id": "kr1.t2"}
    provider = FakeProvider(Script(dedup={"merges": [], "cross_dependencies": [backwards, link]}))

    result = await run_pipeline(_okr(), provider)

    by_id = {t.local_id: t for t in result.tasks}
    assert result.trace.total_retries == 0
    assert by_id["kr1.t1"].depends_on == []
    assert by_id["kr2.t1"].depends_on == ["kr1.t2"]
    assert "always belong to different key results" in _reviews(provider)[0].system


async def test_dedup_that_stays_invalid_keeps_the_plan() -> None:
    cyclic = {
        "merges": [],
        "cross_dependencies": [
            {"task_id": "kr1.t1", "depends_on_id": "kr2.t2"},
            {"task_id": "kr2.t1", "depends_on_id": "kr1.t2"},
        ],
    }
    provider = FakeProvider(Script(dedup=cyclic))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert len(_reviews(provider)) == 3
    assert [t.local_id for t in result.tasks] == ["kr1.t1", "kr1.t2", "kr2.t1", "kr2.t2"]
    assert {t.local_id: t.depends_on for t in result.tasks} == {
        "kr1.t1": [],
        "kr1.t2": ["kr1.t1"],
        "kr2.t1": [],
        "kr2.t2": ["kr2.t1"],
    }


def test_time_budget_derives_daily_and_usable_hours() -> None:
    budget = TimeBudget(working_days=65, total_hours=260)

    assert budget.hours_per_day == 4
    assert budget.usable_hours == 234
    with pytest.raises(ValueError):
        TimeBudget(working_days=0, total_hours=10)


async def test_provider_outage_fails_fast_without_retry_or_switch() -> None:
    provider = FakeProvider(
        Script(**{"check:kr1": ProviderUnavailableError("cannot reach local LLM")}), name="local"
    )

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider)

    failure = caught.value.failure
    assert failure.code == "provider_unavailable"
    assert failure.provider == "local"
    assert failure.suggestions == ["check_connection", "switch_provider"]
    assert [c.kr_id for c in _checks(provider)] == ["kr1", "kr2"]
    assert all(c.attempt == 0 for c in provider.calls)
    assert _calls(provider, "decompose") == []


CLARIFY_QUESTIONS = [
    {"kr_id": "kr1", "question": "Which browsers must the new flow support?", "reason": "scope"},
    {"kr_id": None, "question": "Who signs off the help center content?", "reason": "owner"},
]


async def test_clarify_ok_with_questions_is_retried_as_needs_clarification() -> None:
    contradictory = {"status": "ok", "questions": CLARIFY_QUESTIONS}
    fixed = {"status": "needs_clarification", "questions": CLARIFY_QUESTIONS}
    provider = FakeProvider(Script(check=CHECK_VAGUE, clarify=[contradictory, fixed]))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "needs_clarification"
    assert [q.question for q in result.questions] == [q["question"] for q in CLARIFY_QUESTIONS]
    retry = _asks(provider)[1].user
    assert "status is ok but questions is not empty" in retry
    assert result.trace.total_retries == 1


async def test_clarify_ok_with_questions_asks_back_when_retries_run_out() -> None:
    provider = FakeProvider(
        Script(check=CHECK_VAGUE, clarify={"status": "ok", "questions": CLARIFY_QUESTIONS})
    )

    result = await run_pipeline(_okr(), provider, max_retries=1)

    assert result.status == "needs_clarification"
    assert result.tasks == []
    assert [q.question for q in result.questions] == [q["question"] for q in CLARIFY_QUESTIONS]
    assert [q.kr_id for q in result.questions] == ["kr1", None]
    assert all(q.source == "llm" for q in result.questions)
    assert len(_asks(provider)) == 2
    assert _calls(provider, "decompose") == []


async def test_clarify_ok_with_invalid_questions_still_fails() -> None:
    bad = [{"kr_id": "kr9", "question": "Which KR?", "reason": "unknown id"}]
    provider = FakeProvider(Script(check=CHECK_VAGUE, clarify={"status": "ok", "questions": bad}))

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider, max_retries=1)

    assert caught.value.failure.code == "invalid_llm_output"


def test_key_result_check_quotes_the_end_result_before_the_verdict() -> None:
    schema = strict_json_schema(KeyResultCheck)

    assert list(schema["properties"]) == ["end_result", "concrete"]


async def test_each_key_result_is_checked_on_its_own_and_only_vague_ones_are_asked() -> None:
    okr = _okr(
        clarifications=[ClarificationAnswer(kr_id="kr1", question="Which flow?", answer="Web")]
    )
    question = {"kr_id": "kr2", "question": "Which guides count?", "reason": "vague"}
    provider = FakeProvider(
        Script(
            **{"check:kr2": CHECK_VAGUE},
            clarify={"status": "needs_clarification", "questions": [question]},
        )
    )

    result = await run_pipeline(okr, provider)

    kr1_check, kr2_check = _checks(provider)
    assert json.loads(kr1_check.user) == {
        "key_result": {"id": "kr1", "text": KR_TEXTS["kr1"]},
        "clarifications": [{"question": "Which flow?", "answer": "Web"}],
    }
    assert json.loads(kr2_check.user) == {"key_result": {"id": "kr2", "text": KR_TEXTS["kr2"]}}
    assert "only a direction with no end result" in kr1_check.system
    (ask,) = _asks(provider)
    assert json.loads(ask.user)["vague_key_results"] == [{"id": "kr2", "text": KR_TEXTS["kr2"]}]
    assert [(q.kr_id, q.source) for q in result.questions] == [("kr2", "llm")]


async def test_every_vague_key_result_needs_its_own_question() -> None:
    only_kr1 = {
        "status": "needs_clarification",
        "questions": [{"kr_id": "kr1", "question": "Which flow?", "reason": "vague"}],
    }
    both = {
        "status": "needs_clarification",
        "questions": [
            {"kr_id": "kr1", "question": "Which flow?", "reason": "vague"},
            {"kr_id": "kr2", "question": "Which guides?", "reason": "vague"},
        ],
    }
    provider = FakeProvider(Script(check=CHECK_VAGUE, clarify=[only_kr1, both]))

    result = await run_pipeline(_okr(), provider)

    assert "key result kr2 has no question; ask one about it" in _asks(provider)[1].user
    assert [q.kr_id for q in result.questions] == ["kr1", "kr2"]


async def test_local_timeout_is_retried_once_with_the_same_prompt() -> None:
    timeout = ProviderTimeoutError("local LLM timed out after 180s")
    provider = FakeProvider(Script(**{"decompose:kr1": [timeout, _decompose_ok("kr1")]}))

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    first, second = _calls(provider, "decompose", "kr1")
    assert second.user == first.user
    assert second.attempt == 1
    (kr1_step,) = [s for s in result.trace.steps if s.step == "decompose" and s.kr_id == "kr1"]
    assert kr1_step.retries == 1
    assert kr1_step.errors == ["attempt 1: local LLM timed out after 180s"]


async def test_local_timeout_twice_is_provider_unavailable() -> None:
    timeout = ProviderTimeoutError("local LLM timed out after 180s")
    provider = FakeProvider(Script(**{"decompose:kr1": timeout}))

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider, max_retries=3)

    failure = caught.value.failure
    assert failure.code == "provider_unavailable"
    assert failure.kr_id == "kr1"
    assert failure.attempts == 2
    assert len(_calls(provider, "decompose", "kr1")) == 2


async def test_openai_timeout_is_not_retried_by_the_pipeline() -> None:
    timeout = ProviderTimeoutError("OpenAI timed out after 60s")
    provider = FakeProvider(Script(**{"check:kr1": timeout}), name="openai")

    with pytest.raises(PipelineError) as caught:
        await run_pipeline(_okr(), provider)

    assert caught.value.failure.code == "provider_unavailable"
    assert len([c for c in provider.calls if c.kr_id == "kr1"]) == 1


async def test_local_truncated_answer_is_retried() -> None:
    decompose_bodies: list[dict[str, Any]] = []

    def ollama(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        schema = body["format"]["title"]
        if schema == "KeyResultCheck":
            content: dict[str, Any] = CHECK_CLEAR
        elif schema == "DedupOutput":
            content = DEDUP_NOOP
        elif schema == "KeyResultNeedsOutput":
            content = NEEDS_NONE
        else:
            decompose_bodies.append(body)
            if len(decompose_bodies) == 1:
                return httpx.Response(
                    200, json={"message": {"content": '{"tasks": [{"lo'}, "done_reason": "length"}
                )
            kr_id = "kr1" if 'always "kr1"' in body["messages"][0]["content"] else "kr2"
            content = _decompose_ok(kr_id)
        return httpx.Response(
            200, json={"message": {"content": json.dumps(content)}, "done_reason": "stop"}
        )

    provider = LocalProvider(
        base_url="http://ollama:11434", model="qwen3:8b", transport=httpx.MockTransport(ollama)
    )

    result = await run_pipeline(_okr(), provider)

    assert result.status == "ok"
    assert len(decompose_bodies) == 3
    assert all(b["options"]["num_predict"] == 4096 for b in decompose_bodies)
    assert result.trace.total_retries == 1
    (retried,) = [s for s in result.trace.steps if s.retries]
    assert retried.errors == [
        "attempt 1: response is not valid JSON (response truncated at the token limit)"
    ]


async def test_progress_events_cover_each_stage_and_kr() -> None:
    events: list[ProgressEvent] = []

    async def on_progress(event: ProgressEvent) -> None:
        events.append(event)

    await run_pipeline(_okr(), FakeProvider(Script()), on_progress=on_progress)

    completed_krs = {e.kr_id for e in events if e.stage == "decompose" and e.status == "completed"}
    assert completed_krs == {"kr1", "kr2"}
    last_decompose = [e for e in events if e.stage == "decompose" and e.status == "completed"][-1]
    assert (last_decompose.completed, last_decompose.total) == (2, 2)
    stages = [e.stage for e in events if e.status == "completed" and e.kr_id is None]
    assert stages[:2] == ["precheck", "clarify"]
    assert any(e.stage == "dedup" and e.status == "completed" for e in events)


async def test_progress_reports_retry_and_failure() -> None:
    events: list[ProgressEvent] = []
    provider = FakeProvider(Script(**{"decompose:kr1": InvalidJSONError("bad")}))

    with pytest.raises(PipelineError):
        await run_pipeline(_okr(), provider, on_progress=events.append)

    retries = [e.attempt for e in events if e.status == "retry" and e.kr_id == "kr1"]
    assert retries == [2, 3]
    assert any(e.status == "failed" and e.kr_id == "kr1" for e in events)


async def test_decompose_respects_provider_concurrency() -> None:
    okr = _okr(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="Deliver a smooth first-week experience",
                key_results=[
                    KeyResultInput(id=f"kr{i}", text=f"Ship onboarding improvement number {i}")
                    for i in range(1, 6)
                ],
            )
        ]
    )
    provider = FakeProvider(Script(), name="openai", max_concurrency=2, delay_seconds=0.01)

    result = await run_pipeline(okr, provider)

    assert result.status == "ok"
    assert provider.peak_in_flight == 2


async def test_okr_text_is_not_logged_at_info(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.planner_llm")
    provider = FakeProvider(Script(**{"decompose:kr1": InvalidJSONError("bad")}))

    with pytest.raises(PipelineError):
        await run_pipeline(_okr(), provider)

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert logged
    for text in [*KR_TEXTS.values(), "Deliver a smooth first-week experience"]:
        assert text not in logged
