"""Invariants the scheduler must hold for any calendar, dependency DAG and set of pins."""

import random
import time
from collections import defaultdict
from datetime import date, timedelta
from functools import cache

from hypothesis import given, settings
from hypothesis import strategies as st

from app.calendar import load_holidays, working_days
from app.domain.calendar_config import CalendarConfig
from app.domain.quarter import Quarter
from app.scheduler import ScheduleInput, ScheduleResult, SchedulerTask, schedule
from tests.scheduler_factories import make_input, make_task

PIN_CONFLICT_CODES = {"pinned_overdue", "pinned_outside_quarter", "pinned_non_working_day"}
CAPACITY_CHOICES = [0, 30, 60, 90, 120, 240, 480]


@cache
def vn_holidays() -> frozenset[date]:
    return load_holidays([2026]).holiday_dates


def window_capacity(inp: ScheduleInput) -> dict[date, int]:
    start = max(inp.quarter.start, inp.today)
    return dict(working_days(start, inp.quarter.end, inp.calendar, inp.holidays))


@st.composite
def calendars(draw: st.DrawFn, quarter: Quarter) -> CalendarConfig:
    span = (quarter.end - quarter.start).days
    offsets = st.integers(0, span).map(lambda i: quarter.start + timedelta(days=i))
    leave = draw(st.frozensets(offsets, max_size=15))
    makeup = draw(st.frozensets(offsets, max_size=4)) - leave
    return CalendarConfig(
        weekday_capacity_minutes=draw(st.tuples(*[st.sampled_from(CAPACITY_CHOICES)] * 7)),
        work_saturday=draw(st.booleans()),
        work_sunday=draw(st.booleans()),
        work_holidays=draw(st.booleans()),
        leave_days=leave,
        makeup_days=makeup,
        makeup_day_capacity_minutes=draw(st.sampled_from([60, 240, 480])),
    )


@st.composite
def pins(
    draw: st.DrawFn, quarter: Quarter, capacity: dict[date, int]
) -> tuple[tuple[date, int], ...]:
    """Mostly valid pins on working days; sometimes arbitrary dates to exercise conflicts."""
    valid_days = sorted(capacity)
    around_quarter = st.integers(-5, (quarter.end - quarter.start).days + 5).map(
        lambda i: quarter.start + timedelta(days=i)
    )
    day = st.one_of(st.sampled_from(valid_days), around_quarter) if valid_days else around_quarter
    days = draw(st.lists(day, min_size=1, max_size=3, unique=True))
    return tuple((d, draw(st.integers(1, max(1, capacity.get(d, 240) // 2)))) for d in days)


@st.composite
def schedule_inputs(draw: st.DrawFn, max_tasks: int = 25) -> ScheduleInput:
    quarter = Quarter(year=2026, number=draw(st.integers(1, 4)))
    today = quarter.start + timedelta(days=draw(st.integers(-10, 95)))
    calendar = draw(calendars(quarter))
    base = make_input(today=today, quarter=quarter, calendar=calendar, holidays=vn_holidays())
    capacity = window_capacity(base)

    n = draw(st.integers(0, max_tasks))
    ids = [f"task-{k:02d}" for k in draw(st.permutations(range(n)))]
    done = frozenset(draw(st.lists(st.sampled_from(["done-1", "done-2"]), max_size=2)))
    tasks: list[SchedulerTask] = []
    for i, task_id in enumerate(ids):
        deps = draw(st.frozensets(st.sampled_from(ids[:i]), max_size=3)) if i else frozenset()
        deps |= draw(st.frozensets(st.sampled_from(sorted(done)), max_size=1)) if done else set()
        pinned = draw(pins(quarter, capacity)) if draw(st.integers(0, 5)) == 0 else ()
        tasks.append(
            make_task(
                task_id,
                sum(m for _, m in pinned) or draw(st.integers(1, 900)),
                priority=draw(st.integers(1, 3)),
                kr_order=draw(st.integers(1, 3)),
                order=draw(st.integers(0, 4)),
                deps=deps,
                pins=pinned,
            )
        )
    return base.model_copy(update={"tasks": tuple(tasks), "done_task_ids": done})


def assert_invariants(inp: ScheduleInput, result: ScheduleResult) -> None:
    tasks = {t.id: t for t in inp.tasks}
    placed = {s.task_id: s for s in result.scheduled}
    unscheduled = {u.task_id: u.reason for u in result.unscheduled}
    capacity = window_capacity(inp)
    warned = defaultdict(set)
    for w in result.warnings:
        warned[w.code].add((w.task_ids, w.dates))

    assert placed.keys() | unscheduled.keys() == tasks.keys()
    assert not placed.keys() & unscheduled.keys()

    pinned_per_day: dict[date, int] = defaultdict(int)
    free_per_day: dict[date, int] = defaultdict(int)
    for task_id, s in placed.items():
        task = tasks[task_id]
        days = [a.date for a in s.allocations]
        assert days == sorted(set(days))
        assert (s.start_date, s.end_date) == (days[0], days[-1])
        assert sum(a.minutes for a in s.allocations) == task.estimate_minutes
        assert s.pinned == task.is_pinned
        if task.is_pinned:
            assert s.allocations == task.pinned_allocations
            assert not s.uses_buffer
            for a in s.allocations:
                if a.date in capacity:
                    pinned_per_day[a.date] += a.minutes
                else:
                    assert any(
                        task_id in ids and a.date in dates
                        for code in PIN_CONFLICT_CODES
                        for ids, dates in warned[code]
                    )
        else:
            for a in s.allocations:
                assert a.date in capacity, "allocation on a non-working day or outside the window"
                assert a.date <= inp.quarter.end
                free_per_day[a.date] += a.minutes
            buffer_start = result.feasibility.buffer_start
            assert s.uses_buffer == (buffer_start is not None and s.end_date >= buffer_start)

    over_capacity_days = {d for _, dates in warned["pinned_over_capacity"] for d in dates}
    for day, cap in capacity.items():
        pinned, free = pinned_per_day[day], free_per_day[day]
        assert free <= max(0, cap - pinned)
        assert (pinned > cap) == (day in over_capacity_days)
        if day not in over_capacity_days:
            assert pinned + free <= cap

    conflicts = {ids for ids, _ in warned["pinned_dependency_conflict"]}
    for task_id, task in tasks.items():
        preds = [p for p in task.depends_on if p not in inp.done_task_ids]
        if task_id in unscheduled:
            if unscheduled[task_id] == "dependency_unscheduled":
                assert any(p in unscheduled for p in preds)
            continue
        start = placed[task_id].start_date
        for pred in preds:
            respected = pred in placed and placed[pred].end_date < start
            if task.is_pinned:
                assert respected or (pred, task_id) in conflicts
            else:
                assert respected, f"{pred} -> {task_id} violates end(a) < start(b)"

    feasibility = result.feasibility
    assert feasibility.demand_minutes == sum(t.estimate_minutes for t in inp.tasks)
    assert feasibility.supply_minutes == sum(capacity.values())
    supply, start = feasibility.supply_minutes, feasibility.buffer_start
    assert (start is None) == (supply == 0)
    if start is not None:
        buffer_minutes = sum(c for d, c in capacity.items() if d >= start)
        assert supply - feasibility.buffered_supply_minutes == buffer_minutes
        assert buffer_minutes * 10 >= supply
        assert (buffer_minutes - capacity[start]) * 10 < supply
    assert feasibility.late_task_ids == tuple(sorted(unscheduled))
    levels = {w.level for w in result.warnings}
    expected = "red" if "red" in levels else "yellow" if levels else "green"
    assert feasibility.status == expected


@settings(max_examples=300, deadline=None)
@given(schedule_inputs())
def test_schedule_respects_all_invariants(inp: ScheduleInput) -> None:
    assert_invariants(inp, schedule(inp))


@settings(max_examples=150, deadline=None)
@given(schedule_inputs(), st.randoms(use_true_random=False))
def test_same_input_in_any_task_order_gives_identical_result(
    inp: ScheduleInput, rnd: random.Random
) -> None:
    shuffled = list(inp.tasks)
    rnd.shuffle(shuffled)
    reordered = inp.model_copy(update={"tasks": tuple(shuffled)})
    first = schedule(inp)
    assert schedule(inp) == first
    assert schedule(reordered) == first


@settings(max_examples=100, deadline=None)
@given(schedule_inputs(max_tasks=15))
def test_higher_objective_is_never_displaced_by_lower_objective(inp: ScheduleInput) -> None:
    """Dropping every lower-priority objective must not change where the top objective lands."""
    free = [t for t in inp.tasks if not t.is_pinned and not t.depends_on]
    if not free:
        return
    top = min(t.objective_priority for t in free)
    only_top = inp.model_copy(
        update={"tasks": tuple(t for t in free if t.objective_priority == top)}
    )
    mixed = inp.model_copy(update={"tasks": tuple(free)})
    top_ids = {t.id for t in only_top.tasks}
    alone = {s.task_id: s for s in schedule(only_top).scheduled}
    together = {s.task_id: s for s in schedule(mixed).scheduled if s.task_id in top_ids}
    assert together == alone


def benchmark_input() -> ScheduleInput:
    """3 objectives x 3 KRs x 60 tasks, chained in pairs inside each KR."""
    tasks = []
    for o in range(1, 4):
        for k in range(1, 4):
            for t in range(60):
                task_id = f"o{o}-k{k}-t{t:02d}"
                deps = [f"o{o}-k{k}-t{t - 1:02d}"] if t % 2 else []
                tasks.append(
                    make_task(
                        task_id, 120 + 60 * (t % 5), priority=o, kr_order=k, order=t, deps=deps
                    )
                )
    return make_input(*tasks, holidays=vn_holidays())


def test_benchmark_three_objectives_three_krs_sixty_tasks_under_200ms() -> None:
    inp = benchmark_input()
    schedule(inp)
    elapsed = []
    for _ in range(3):
        started = time.perf_counter()
        result = schedule(inp)
        elapsed.append(time.perf_counter() - started)
    assert len(result.scheduled) + len(result.unscheduled) == 540
    assert min(elapsed) < 0.2, f"best of 3 runs took {min(elapsed) * 1000:.1f} ms"
