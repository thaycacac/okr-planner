"""Expected KR values follow the schedule: monotonic, and exactly the target once done."""

from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.domain.quarter import Quarter
from app.scheduler import Allocation, MilestoneTask, kr_milestones
from app.scheduler.milestones import expected_value, month_ends, week_ends

Q4 = Quarter(year=2026, number=4)


def _scheduled_task(offsets: list[int], minutes: int) -> MilestoneTask:
    days = sorted({Q4.start + timedelta(days=o) for o in offsets})
    return MilestoneTask(
        estimate_minutes=minutes * len(days),
        allocations=tuple(Allocation(date=d, minutes=minutes) for d in days),
    )


tasks_strategy = st.lists(
    st.builds(
        _scheduled_task,
        st.lists(st.integers(0, 91), min_size=1, max_size=6),
        st.integers(1, 480),
    ),
    min_size=1,
    max_size=8,
)
values = st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False)


@given(tasks_strategy, values, values)
def test_milestones_are_monotonic_and_end_at_the_target(
    tasks: list[MilestoneTask], baseline: float, target: float
) -> None:
    result = kr_milestones(Q4, tuple(tasks), baseline, target)
    assert result.planned_minutes == result.total_minutes
    finish = max(a.date for t in tasks for a in t.allocations)
    assert result.expected_completion == finish
    for series in (result.weekly, result.monthly):
        expected = [c.expected_value for c in series]
        assert all(v is not None for v in expected)
        ordered = sorted(expected, reverse=target < baseline)  # type: ignore[type-var]
        assert expected == ordered
        assert expected[-1] == target
        progress = [c.progress for c in series]
        assert progress == sorted(progress) and progress[-1] == 1
        assert all(c.expected_value == target for c in series if c.period_end >= finish)


def test_unfinished_schedule_never_reaches_the_target() -> None:
    task = MilestoneTask(
        estimate_minutes=600, allocations=(Allocation(date=date(2026, 10, 5), minutes=240),)
    )
    result = kr_milestones(Q4, (task,), 0, 100)
    assert result.expected_completion is None
    assert result.planned_minutes == 240
    assert result.monthly[-1].expected_value == 40


def test_done_tasks_count_from_their_finish_date() -> None:
    done = MilestoneTask(estimate_minutes=300, done_on=date(2026, 10, 20))
    later = MilestoneTask(
        estimate_minutes=300, allocations=(Allocation(date=date(2026, 11, 10), minutes=300),)
    )
    result = kr_milestones(Q4, (done, later), 10, 20)
    assert [c.expected_value for c in result.monthly] == [15, 20, 20]
    assert result.expected_completion == date(2026, 11, 10)


def test_stale_allocations_beyond_a_lowered_estimate_are_capped() -> None:
    lowered = MilestoneTask(
        estimate_minutes=960,
        allocations=tuple(
            Allocation(date=date(2026, 10, 5) + timedelta(days=i), minutes=340) for i in range(3)
        ),
    )
    other = MilestoneTask(
        estimate_minutes=240, allocations=(Allocation(date=date(2026, 11, 2), minutes=240),)
    )
    result = kr_milestones(Q4, (lowered, other), 0, 100)
    assert result.total_minutes == result.planned_minutes == 1200
    assert result.expected_completion == date(2026, 11, 2)
    october = result.monthly[0]
    assert october.completed_minutes == 960
    assert october.progress == 0.8
    assert october.expected_value == 80
    for series in (result.weekly, result.monthly):
        assert all(0 <= c.progress <= 1 for c in series)
        assert all(c.completed_minutes <= result.total_minutes for c in series)
        assert series[-1].progress == 1


def test_over_allocated_task_finishes_when_its_estimate_is_reached() -> None:
    task = MilestoneTask(
        estimate_minutes=400,
        allocations=(
            Allocation(date=date(2026, 10, 5), minutes=300),
            Allocation(date=date(2026, 10, 12), minutes=300),
            Allocation(date=date(2026, 10, 19), minutes=300),
        ),
    )
    result = kr_milestones(Q4, (task,), 0, 10)
    assert result.expected_completion == date(2026, 10, 12)
    assert result.planned_minutes == 400
    assert result.monthly[-1].progress == 1


def test_value_is_none_without_numbers() -> None:
    assert expected_value(None, 10, 1, 2) is None
    assert expected_value(0, 10, 0, 0) is None
    assert expected_value(0, 10, 1, 4) == 2.5


def test_period_ends() -> None:
    assert month_ends(Q4) == [date(2026, 10, 31), date(2026, 11, 30), date(2026, 12, 31)]
    weeks = week_ends(Q4)
    assert weeks[0] == date(2026, 10, 4)
    assert weeks[-1] == date(2026, 12, 31)
    assert all(d.weekday() == 6 for d in weeks[:-1])
