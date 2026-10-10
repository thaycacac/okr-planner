"""Acceptance criterion 2: nothing is scheduled after the last day of the quarter (or before
today), and every task starts only after all of its prerequisites have finished."""

from datetime import date

from sqlalchemy import Engine

from tests.acceptance.support import (
    PlanLLM,
    allocation_days,
    assert_schedule_invariants,
    create_objective,
    create_quarter,
    plan_quarter,
    schedule_of,
    tasks_of,
)
from tests.api_support import ApiHarness

QUARTER_END = "2026-12-31"


def _objectives(api: ApiHarness, quarter_id: int) -> None:
    create_objective(
        api,
        quarter_id,
        "Tăng trưởng người dùng trả phí",
        "high",
        ["Ra mắt luồng onboarding mới", "Tối ưu trang giá"],
    )
    create_objective(
        api,
        quarter_id,
        "Ổn định hạ tầng thanh toán",
        "low",
        ["Giảm lỗi thanh toán thất bại", "Theo dõi cảnh báo thanh toán"],
    )


def test_work_that_does_not_fit_stays_unscheduled_instead_of_passing_quarter_end(
    api: ApiHarness,
) -> None:
    api.provider.handler = PlanLLM(tasks_per_kr=25, hours=6)
    quarter_id = create_quarter(api)
    _objectives(api, quarter_id)
    plan_quarter(api, quarter_id)

    schedule = schedule_of(api, quarter_id)
    tasks = tasks_of(api, quarter_id)
    assert_schedule_invariants(schedule, tasks)

    assert schedule["window_end"] == QUARTER_END
    assert max(allocation_days(schedule)) == QUARTER_END
    scheduled = sum(d["scheduled_minutes"] for d in schedule["days"])
    assert scheduled <= schedule["feasibility"]["supply_minutes"]
    reasons = {u["reason"] for u in schedule["unscheduled"]}
    assert reasons == {"exceeds_quarter", "dependency_unscheduled"}
    assert len(schedule["tasks"]) + len(schedule["unscheduled"]) == len(tasks) == 100


def test_dependencies_finish_before_dependents_start_even_across_key_results(
    api: ApiHarness,
) -> None:
    api.provider.handler = PlanLLM(tasks_per_kr=4, hours=5, cross_kr=True)
    quarter_id = create_quarter(api)
    _objectives(api, quarter_id)
    plan_quarter(api, quarter_id)

    schedule = schedule_of(api, quarter_id)
    tasks = tasks_of(api, quarter_id)
    assert_schedule_invariants(schedule, tasks)

    kr_of = {t["id"]: t["key_result_id"] for t in tasks}
    edges = [(pred, t["id"]) for t in tasks for pred in t["depends_on"]]
    cross = [(a, b) for a, b in edges if kr_of[a] != kr_of[b]]
    assert len(edges) == 4 * 3 + 2 and len(cross) == 2
    placed = {t["task_id"]: t for t in schedule["tasks"]}
    assert schedule["unscheduled"] == []
    for pred, task in edges:
        assert placed[pred]["end_date"] < placed[task]["start_date"], (pred, task)


def test_quarter_already_under_way_is_scheduled_from_today(db_engine: Engine) -> None:
    today = date(2026, 11, 16)
    with ApiHarness.start(db_engine, today=today) as api:
        api.provider.handler = PlanLLM(tasks_per_kr=6, hours=6)
        quarter_id = create_quarter(api)
        _objectives(api, quarter_id)
        plan_quarter(api, quarter_id)

        schedule = schedule_of(api, quarter_id)
        assert_schedule_invariants(schedule, tasks_of(api, quarter_id))
        assert (schedule["window_start"], schedule["window_end"]) == ("2026-11-16", QUARTER_END)
        used = allocation_days(schedule)
        assert min(used) == "2026-11-16" and max(used) <= QUARTER_END
