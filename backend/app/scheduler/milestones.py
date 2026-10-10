"""Expected value of a numeric key result at the end of each week and month.

The value follows the schedule, not the calendar: at a checkpoint the KR is expected to have
moved from baseline towards target by the share of its task minutes finished by then
(scheduled minutes up to that date, plus tasks already done). It is an expectation if the plan
is followed, not a forecast.
"""

import calendar as month_calendar
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field

from app.domain.quarter import Quarter
from app.scheduler.models import Allocation

SUNDAY = 6


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MilestoneTask(_Frozen):
    """``done_on`` is set for a finished task; otherwise ``allocations`` is its schedule."""

    estimate_minutes: int = Field(gt=0)
    done_on: date | None = None
    allocations: tuple[Allocation, ...] = ()


class Checkpoint(_Frozen):
    period_end: date
    completed_minutes: int
    progress: float = Field(ge=0, le=1)
    expected_value: float | None


class KrMilestones(_Frozen):
    total_minutes: int
    planned_minutes: int = Field(description="Minutes done or scheduled inside the quarter")
    expected_completion: date | None = Field(
        description="Last day of work when every task is done or scheduled, else None"
    )
    weekly: tuple[Checkpoint, ...]
    monthly: tuple[Checkpoint, ...]


def week_ends(quarter: Quarter) -> list[date]:
    """Every Sunday of the quarter, plus the quarter end when it is not a Sunday."""
    first = quarter.start + timedelta(days=(SUNDAY - quarter.start.weekday()) % 7)
    ends = []
    day = first
    while day <= quarter.end:
        ends.append(day)
        day += timedelta(days=7)
    if not ends or ends[-1] != quarter.end:
        ends.append(quarter.end)
    return ends


def month_ends(quarter: Quarter) -> list[date]:
    ends = []
    for month in range(quarter.start.month, quarter.end.month + 1):
        last = month_calendar.monthrange(quarter.year, month)[1]
        ends.append(date(quarter.year, month, last))
    return ends


def _task_completed_by(task: MilestoneTask, day: date) -> int:
    """A stale schedule can hold more minutes than a since-lowered estimate; a task never
    counts for more than its estimate."""
    if task.done_on is not None:
        return task.estimate_minutes if task.done_on <= day else 0
    scheduled = sum(a.minutes for a in task.allocations if a.date <= day)
    return min(scheduled, task.estimate_minutes)


def _completed_by(tasks: tuple[MilestoneTask, ...], day: date) -> int:
    return sum(_task_completed_by(task, day) for task in tasks)


def _finish_day(task: MilestoneTask) -> date | None:
    """Day the task's estimate is fully done or scheduled, None when it never is."""
    if task.done_on is not None:
        return task.done_on
    scheduled = 0
    for allocation in sorted(task.allocations, key=lambda a: a.date):
        scheduled += allocation.minutes
        if scheduled >= task.estimate_minutes:
            return allocation.date
    return None


def expected_value(
    baseline: float | None, target: float | None, completed: int, total: int
) -> float | None:
    """Linear in the finished share; exactly ``target`` once everything is finished and clamped
    between baseline and target so float rounding can never overshoot."""
    if baseline is None or target is None or total == 0:
        return None
    if completed >= total:
        return target
    value = baseline + (target - baseline) * completed / total
    return min(max(value, min(baseline, target)), max(baseline, target))


def kr_milestones(
    quarter: Quarter,
    tasks: tuple[MilestoneTask, ...],
    baseline: float | None = None,
    target: float | None = None,
) -> KrMilestones:
    total = sum(t.estimate_minutes for t in tasks)

    def checkpoints(ends: list[date]) -> tuple[Checkpoint, ...]:
        result = []
        for end in ends:
            completed = _completed_by(tasks, end)
            result.append(
                Checkpoint(
                    period_end=end,
                    completed_minutes=completed,
                    progress=completed / total if total else 0.0,
                    expected_value=expected_value(baseline, target, completed, total),
                )
            )
        return tuple(result)

    planned = _completed_by(tasks, quarter.end)
    finish_days = [_finish_day(t) for t in tasks]
    complete = bool(tasks) and all(d is not None for d in finish_days)
    return KrMilestones(
        total_minutes=total,
        planned_minutes=planned,
        expected_completion=max(d for d in finish_days if d is not None) if complete else None,
        weekly=checkpoints(week_ends(quarter)),
        monthly=checkpoints(month_ends(quarter)),
    )
