"""Scheduler input/output contracts; durations are whole minutes so capacity checks stay exact."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.calendar_config import MINUTES_PER_DAY, CalendarConfig
from app.domain.quarter import Quarter

TaskId = Annotated[str, Field(min_length=1)]
WarningLevel = Literal["yellow", "red"]
FeasibilityStatus = Literal["green", "yellow", "red"]
WarningCode = Literal[
    "uses_buffer",
    "exceeds_quarter",
    "dependency_unscheduled",
    "pinned_over_capacity",
    "pinned_non_working_day",
    "pinned_overdue",
    "pinned_outside_quarter",
    "pinned_dependency_conflict",
]
UnscheduledReason = Literal["exceeds_quarter", "dependency_unscheduled"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Allocation(_Frozen):
    date: date
    minutes: int = Field(gt=0, le=MINUTES_PER_DAY)


class SchedulerTask(_Frozen):
    """An unfinished task; one with ``pinned_allocations`` is fixed by the user and never moved."""

    id: TaskId
    objective_id: TaskId
    kr_id: TaskId
    estimate_minutes: int = Field(gt=0)
    objective_priority: int
    kr_order: int
    task_order: int
    depends_on: frozenset[TaskId] = frozenset()
    pinned_allocations: tuple[Allocation, ...] = ()

    @field_validator("pinned_allocations")
    @classmethod
    def _sort_pins(cls, value: tuple[Allocation, ...]) -> tuple[Allocation, ...]:
        return tuple(sorted(value, key=lambda a: a.date))

    @model_validator(mode="after")
    def _pins_cover_estimate(self) -> Self:
        if not self.pinned_allocations:
            return self
        dates = [a.date for a in self.pinned_allocations]
        if len(dates) != len(set(dates)):
            raise ValueError(f"task {self.id!r} pins the same date more than once")
        pinned_total = sum(a.minutes for a in self.pinned_allocations)
        if pinned_total != self.estimate_minutes:
            raise ValueError(
                f"task {self.id!r} pins {pinned_total} minutes but estimates "
                f"{self.estimate_minutes}"
            )
        return self

    @property
    def is_pinned(self) -> bool:
        return bool(self.pinned_allocations)

    @property
    def priority_key(self) -> tuple[int, int, int, str]:
        return (self.objective_priority, self.kr_order, self.task_order, self.id)


class ScheduleInput(_Frozen):
    """``tasks`` are the unfinished tasks of every active OKR in the quarter.

    ``done_task_ids`` lists finished tasks that ``depends_on`` may still reference; such
    dependencies count as satisfied. ``holidays`` comes from ``app.calendar.load_holidays``.
    """

    quarter: Quarter
    today: date
    # Already folded into ``today``; kept so a changed start date alters the input fingerprint.
    plan_start: date | None = None
    calendar: CalendarConfig = CalendarConfig()
    holidays: frozenset[date] = frozenset()
    tasks: tuple[SchedulerTask, ...] = ()
    done_task_ids: frozenset[TaskId] = frozenset()


class ScheduledTask(_Frozen):
    task_id: str
    start_date: date
    end_date: date
    allocations: tuple[Allocation, ...]
    pinned: bool
    uses_buffer: bool


class UnscheduledTask(_Frozen):
    task_id: str
    reason: UnscheduledReason


class ScheduleWarning(_Frozen):
    """Machine-readable warning; the UI renders the localized text from ``code``."""

    code: WarningCode
    level: WarningLevel
    task_ids: tuple[str, ...] = ()
    dates: tuple[date, ...] = ()


class Feasibility(_Frozen):
    """D = demand of all input tasks, S = capacity of the scheduling window.

    The 10% buffer is whole days from ``buffer_start`` to the window end;
    ``buffered_supply_minutes`` is the capacity before ``buffer_start``.
    """

    status: FeasibilityStatus
    demand_minutes: int
    supply_minutes: int
    buffered_supply_minutes: int
    buffer_start: date | None
    late_task_ids: tuple[str, ...]
    late_kr_ids: tuple[str, ...]
    late_objective_ids: tuple[str, ...]


class ScheduleResult(_Frozen):
    window_start: date
    window_end: date
    scheduled: tuple[ScheduledTask, ...]
    unscheduled: tuple[UnscheduledTask, ...]
    warnings: tuple[ScheduleWarning, ...]
    feasibility: Feasibility
