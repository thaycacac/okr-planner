"""Acceptance criterion 6: an overloaded quarter is flagged with a warning and concrete options,
and the scheduler leaves the extra tasks out instead of cramming them into full days.

Q4/2026 from 2026-10-01, Monday to Friday 4h, holiday 2026-11-24: 260 hours of capacity.
"""

from typing import Any

from tests.acceptance.support import (
    PlanLLM,
    assert_schedule_invariants,
    create_objective,
    create_quarter,
    plan_quarter,
    schedule_of,
    tasks_of,
)
from tests.api_support import ApiHarness

H = 60
SUPPLY = 260 * H


def _quarter(api: ApiHarness, high_tasks: int, low_tasks: int) -> tuple[int, int, int]:
    """Two objectives of two KRs each; every KR gets independent 6-hour tasks."""
    quarter_id = create_quarter(api)
    high = create_objective(
        api,
        quarter_id,
        "Ra mắt sản phẩm di động",
        "high",
        ["Phát hành bản iOS", "Phát hành bản Android"],
    )
    low = create_objective(
        api,
        quarter_id,
        "Tự học kỹ năng quản lý",
        "low",
        ["Đọc sách quản lý", "Tham gia khóa huấn luyện"],
    )
    counts = {f"kr{kr['id']}": high_tasks for kr in high["key_results"]}
    counts |= {f"kr{kr['id']}": low_tasks for kr in low["key_results"]}
    api.provider.handler = PlanLLM(hours=6, chain=False, tasks_by_kr=counts)
    plan_quarter(api, quarter_id)
    return quarter_id, high["id"], low["id"]


def _red(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    return [w for w in schedule["warnings"] if w["level"] == "red"]


def test_overloaded_quarter_is_flagged_red_and_extra_tasks_are_left_out(api: ApiHarness) -> None:
    quarter_id, high_id, low_id = _quarter(api, high_tasks=20, low_tasks=10)
    schedule = schedule_of(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    feasibility = schedule["feasibility"]
    assert feasibility["status"] == "red"
    assert (feasibility["demand_minutes"], feasibility["supply_minutes"]) == (360 * H, SUPPLY)
    warnings = {w["code"]: w for w in schedule["warnings"]}
    unscheduled = {u["task_id"]: u["reason"] for u in schedule["unscheduled"]}
    assert warnings["exceeds_quarter"]["level"] == "red"
    assert set(warnings["exceeds_quarter"]["task_ids"]) == {
        t for t, reason in unscheduled.items() if reason == "exceeds_quarter"
    }
    assert set(feasibility["late_task_ids"]) == unscheduled.keys()
    assert feasibility["late_objective_ids"] == [low_id]
    assert {t["objective_id"] for t in schedule["tasks"]} >= {high_id}

    scheduled = sum(d["scheduled_minutes"] for d in schedule["days"])
    assert scheduled <= SUPPLY
    assert all(d["scheduled_minutes"] <= d["capacity_minutes"] for d in schedule["days"])


def test_overload_comes_with_options_computed_by_the_scheduler(api: ApiHarness) -> None:
    quarter_id, _, low_id = _quarter(api, high_tasks=20, low_tasks=10)
    before = schedule_of(api, quarter_id)

    response = api.client.get(f"/quarters/{quarter_id}/options")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["overloaded"] is True
    late = set(body["current"]["feasibility"]["late_task_ids"])
    estimates = {t["id"]: t["estimate_minutes"] for t in tasks_of(api, quarter_id)}
    assert body["current"]["shortfall_minutes"] == sum(estimates[t] for t in late)
    assert body["current"]["shortfall_minutes"] >= 360 * H - SUPPLY
    assert {o["group"] for o in body["options"]} == {"more_time", "less_scope", "defer"}
    for option in body["options"]:
        outcome = option["outcome"]
        assert outcome["feasibility"]["status"] in ("green", "yellow", "red"), option["id"]
        assert outcome["resolves_overload"] == (outcome["feasibility"]["status"] != "red")
    assert any(o["outcome"]["resolves_overload"] for o in body["options"])
    hint = body["weekday_hint"]
    assert hint["min_extra_minutes_not_red"] <= hint["min_extra_minutes_green"]

    pause = f"drop_objective:{low_id}"
    evaluated = api.client.post(
        f"/quarters/{quarter_id}/options/evaluate", json={"option_ids": [pause]}
    )
    assert evaluated.status_code == 200, evaluated.text
    after = evaluated.json()["after"]
    assert after["feasibility"]["status"] != "red" and after["late_task_count"] == 0

    unchanged = schedule_of(api, quarter_id)
    assert unchanged["id"] == before["id"] and unchanged["feasibility"]["status"] == "red"


def test_options_change_the_plan_only_when_applied_and_can_be_undone(api: ApiHarness) -> None:
    quarter_id, _, _ = _quarter(api, high_tasks=20, low_tasks=10)
    hint = api.client.get(f"/quarters/{quarter_id}/options").json()["weekday_hint"]
    option = f"weekday_minutes:+{hint['min_extra_minutes_not_red']}"

    applied = api.client.post(
        f"/quarters/{quarter_id}/options/apply",
        json={"option_ids": [option]},
        headers={"Idempotency-Key": "acceptance-overload"},
    )
    assert applied.status_code == 200, applied.text
    application = applied.json()
    schedule = schedule_of(api, quarter_id)
    assert schedule == application["schedule"]
    assert _red(schedule) == [] and schedule["unscheduled"] == []
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    undone = api.client.post(f"/option-applications/{application['id']}/undo")
    assert undone.status_code == 200, undone.text
    assert undone.json()["schedule"]["feasibility"]["status"] == "red"


def test_tight_quarter_uses_the_buffer_with_a_yellow_warning(api: ApiHarness) -> None:
    quarter_id, _, _ = _quarter(api, high_tasks=10, low_tasks=10)
    schedule = schedule_of(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    assert schedule["feasibility"]["status"] == "yellow"
    assert schedule["feasibility"]["demand_minutes"] == 240 * H
    assert [w["code"] for w in schedule["warnings"]] == ["uses_buffer"]
    buffered = {t["task_id"] for t in schedule["tasks"] if t["uses_buffer"]}
    assert buffered and set(schedule["warnings"][0]["task_ids"]) == buffered
    assert schedule["unscheduled"] == []
