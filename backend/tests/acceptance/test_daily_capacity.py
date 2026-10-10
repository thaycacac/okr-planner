"""Acceptance criterion 3: the hours scheduled on any day never exceed that day's capacity,
with several OKRs sharing the calendar and tasks spread over several days."""

import random
from collections import defaultdict
from datetime import date

import pytest

from app.calendar.working_days import day_capacity_minutes
from app.domain.calendar_config import CalendarConfig
from app.scheduler import schedule
from tests.acceptance.support import (
    PlanLLM,
    assert_schedule_invariants,
    calendar_body,
    create_objective,
    create_quarter,
    load_by_day,
    plan_quarter,
    schedule_of,
    set_global_calendar,
    tasks_of,
    weekday_of,
)
from tests.api_support import ApiHarness
from tests.scheduler_factories import make_input, make_task

UNEVEN = {"mon": 120, "tue": 300, "wed": 240, "thu": 90, "fri": 360, "sat": 0, "sun": 0}
WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def test_several_okrs_with_multi_day_tasks_never_overfill_a_day(api: ApiHarness) -> None:
    set_global_calendar(api, calendar_body(UNEVEN))
    api.provider.handler = PlanLLM(
        tasks_per_kr=5, hours=5.5, hours_by_kr={"kr1": 6, "kr4": 2.5}, cross_kr=True
    )
    quarter_id = create_quarter(api)
    for title, priority in (
        ("Mở rộng kênh bán hàng B2B", "high"),
        ("Hoàn thành chứng chỉ AWS", "medium"),
        ("Duy trì sức khỏe để làm việc bền bỉ", "low"),
    ):
        create_objective(
            api, quarter_id, title, priority, [f"{title}: kết quả 1", f"{title}: kết quả 2"]
        )
    plan_quarter(api, quarter_id)

    result = schedule_of(api, quarter_id)
    tasks = tasks_of(api, quarter_id)
    assert_schedule_invariants(result, tasks)
    assert result["unscheduled"] == []

    load = load_by_day(result)
    for day, minutes in load.items():
        assert minutes <= UNEVEN[WEEKDAY_KEYS[weekday_of(day)]], day
    assert any(load[d] == UNEVEN[WEEKDAY_KEYS[weekday_of(d)]] for d in load)

    multi_day = [t for t in result["tasks"] if len(t["allocations"]) > 1]
    assert len(multi_day) >= len(result["tasks"]) // 2
    objectives_by_day: dict[str, set[int]] = defaultdict(set)
    for task in result["tasks"]:
        for allocation in task["allocations"]:
            objectives_by_day[allocation["date"]].add(task["objective_id"])
    assert any(len(ids) > 1 for ids in objectives_by_day.values()), "no day is shared by OKRs"


@pytest.mark.parametrize("seed", range(40))
def test_random_multi_okr_quarters_never_overfill_a_day(seed: int) -> None:
    rng = random.Random(seed)
    capacity = tuple(rng.choice((0, 60, 90, 120, 240, 360, 480)) for _ in range(7))
    calendar = CalendarConfig(
        weekday_capacity_minutes=capacity,
        work_saturday=rng.random() < 0.3,
        work_sunday=rng.random() < 0.3,
        work_holidays=rng.random() < 0.3,
        leave_days=frozenset(date(2026, 10, rng.randint(1, 31)) for _ in range(3)),
    )
    holidays = {date(2026, 11, 24), date(2026, 12, rng.randint(1, 31))}
    tasks = []
    for objective in range(1, rng.randint(2, 5)):
        for kr in range(1, rng.randint(2, 4)):
            ids: list[str] = []
            for n in range(rng.randint(1, 8)):
                task_id = f"o{objective}-kr{kr}-t{n}"
                deps = [rng.choice(ids)] if ids and rng.random() < 0.6 else []
                tasks.append(
                    make_task(
                        task_id,
                        rng.randint(1, 12) * 30,
                        priority=objective,
                        kr_order=kr,
                        order=n,
                        deps=deps,
                    )
                )
                ids.append(task_id)
    inp = make_input(*tasks, calendar=calendar, holidays=holidays)

    result = schedule(inp)

    load: dict[date, int] = defaultdict(int)
    for placed in result.scheduled:
        for allocation in placed.allocations:
            load[allocation.date] += allocation.minutes
    for day, minutes in load.items():
        assert minutes <= day_capacity_minutes(day, calendar, holidays), day
    assert sum(load.values()) <= result.feasibility.supply_minutes
