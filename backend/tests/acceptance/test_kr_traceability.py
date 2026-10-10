"""Acceptance criterion 4: every key result gets at least one task, and every task (stored,
scheduled or left unscheduled) traces back to exactly one key result of its objective."""

from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.fake import FakeReply
from tests.acceptance.support import (
    PlanLLM,
    create_objective,
    create_quarter,
    plan_quarter,
    run_plan,
    schedule_of,
    tasks_of,
)
from tests.api_support import ApiHarness


def _okr(api: ApiHarness) -> tuple[int, dict[int, int]]:
    """Three objectives with five KRs; returns the quarter and ``{kr_id: objective_id}``."""
    quarter_id = create_quarter(api)
    owners: dict[int, int] = {}
    for title, priority, krs in (
        ("Tăng trưởng người dùng trả phí", "high", ["Ra mắt gói Team", "Tối ưu trang giá"]),
        ("Nâng cao độ tin cậy hệ thống", "medium", ["Thêm giám sát thanh toán"]),
        (
            "Phát triển kỹ năng đội ngũ",
            "low",
            ["Hoàn thành khóa học AWS", "Tổ chức buổi chia sẻ nội bộ"],
        ),
    ):
        objective = create_objective(api, quarter_id, title, priority, list(krs))
        owners.update({kr["id"]: objective["id"] for kr in objective["key_results"]})
    return quarter_id, owners


def test_every_key_result_gets_tasks_and_every_task_traces_to_its_key_result(
    api: ApiHarness,
) -> None:
    api.provider.handler = PlanLLM(tasks_per_kr=3, hours=4, cross_kr=True)
    quarter_id, owners = _okr(api)
    run = plan_quarter(api, quarter_id)

    tasks = tasks_of(api, quarter_id)
    assert run["task_count"] == len(tasks) == 3 * len(owners)
    assert {t["key_result_id"] for t in tasks} == owners.keys()
    for task in tasks:
        assert task["objective_id"] == owners[task["key_result_id"]], task
        assert task["plan_run_id"] == run["id"]

    detail = api.client.get(f"/quarters/{quarter_id}").json()
    for objective in detail["objectives"]:
        for kr in objective["key_results"]:
            assert kr["tasks"], f"KR {kr['id']} has no task"
            assert {t["key_result_id"] for t in kr["tasks"]} == {kr["id"]}

    schedule = schedule_of(api, quarter_id)
    entries = schedule["tasks"] + schedule["unscheduled"]
    assert {e["task_id"] for e in entries} == {t["id"] for t in tasks}
    for entry in entries:
        assert entry["objective_id"] == owners[entry["key_result_id"]], entry


def test_key_result_left_without_tasks_by_the_llm_is_asked_again(api: ApiHarness) -> None:
    plan = PlanLLM(tasks_per_kr=2)
    empty_once: set[str | None] = set()

    def handler(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if prompt.step == "decompose" and prompt.kr_id not in empty_once:
            empty_once.add(prompt.kr_id)
            return {"tasks": []}
        return plan(prompt, schema)

    api.provider.handler = handler
    quarter_id, owners = _okr(api)
    run = plan_quarter(api, quarter_id)

    decompose = [c for c in api.provider.calls if c.step == "decompose"]
    assert len(decompose) == 2 * len(owners)
    assert all("at least one task" in c.user for c in decompose if c.attempt)
    assert run["total_retries"] == len(owners)
    assert {t["key_result_id"] for t in tasks_of(api, quarter_id)} == owners.keys()


def test_plan_fails_instead_of_storing_a_key_result_without_tasks(api: ApiHarness) -> None:
    plan = PlanLLM(tasks_per_kr=2)
    quarter_id, owners = _okr(api)
    starved = f"kr{max(owners)}"

    def handler(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if prompt.step == "decompose" and prompt.kr_id == starved:
            return {"tasks": []}
        return plan(prompt, schema)

    api.provider.handler = handler
    job_id, events = run_plan(api, quarter_id=quarter_id, skip_clarification=True)

    assert events[-1]["run_status"] == "failed"
    run: dict[str, Any] = api.client.get(f"/plans/{job_id}").json()
    assert run["error"]["code"] == "invalid_llm_output"
    assert (run["error"]["step"], run["error"]["key_result_id"]) == ("decompose", max(owners))
    assert run["task_count"] == 0
    assert tasks_of(api, quarter_id) == []
    assert api.client.get(f"/quarters/{quarter_id}/schedule").status_code == 404


def test_tasks_pointing_at_another_key_result_are_rejected(api: ApiHarness) -> None:
    plan = PlanLLM(tasks_per_kr=2)
    wrong_once: set[str | None] = set()

    def handler(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        reply = plan(prompt, schema)
        if prompt.step == "decompose" and prompt.kr_id not in wrong_once:
            wrong_once.add(prompt.kr_id)
            assert isinstance(reply, dict)
            reply["tasks"][0]["kr_id"] = "kr999"
        return reply

    api.provider.handler = handler
    quarter_id, owners = _okr(api)
    plan_quarter(api, quarter_id)

    retried = [c for c in api.provider.calls if c.step == "decompose" and c.attempt]
    assert len(retried) == len(owners)
    assert all("kr_id 'kr999' is not valid" in c.user for c in retried)
    tasks = tasks_of(api, quarter_id)
    assert all(t["objective_id"] == owners[t["key_result_id"]] for t in tasks)
