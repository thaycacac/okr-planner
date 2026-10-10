"""Deterministic list scheduler (see docs/adr/0003-scheduler-deterministic.md)."""

from bisect import bisect_left
from collections import defaultdict
from datetime import date, timedelta

from app.calendar.working_days import WorkingDay, working_days
from app.scheduler.graph import priority_topological_order, validate_references
from app.scheduler.models import (
    Allocation,
    Feasibility,
    FeasibilityStatus,
    ScheduledTask,
    ScheduleInput,
    ScheduleResult,
    SchedulerTask,
    ScheduleWarning,
    UnscheduledReason,
    UnscheduledTask,
    WarningCode,
    WarningLevel,
)

ONE_DAY = timedelta(days=1)


def buffer_start_index(capacities: list[int]) -> int | None:
    """Index of the first buffer day: the shortest suffix holding at least 10% of supply.

    The buffer is rounded up to whole days, so it usually holds a bit more than 10%.
    ``None`` when there is no supply at all.
    """
    supply = sum(capacities)
    if supply == 0:
        return None
    suffix = 0
    for index in range(len(capacities) - 1, -1, -1):
        suffix += capacities[index]
        if suffix * 10 >= supply:
            return index
    return 0


class _Planner:
    def __init__(self, inp: ScheduleInput, days: list[WorkingDay]) -> None:
        self.inp = inp
        self.window_start = max(inp.quarter.start, inp.today)
        self.window_end = inp.quarter.end
        self.days = days
        self.dates = [d.date for d in days]
        self.index = {d.date: i for i, d in enumerate(days)}
        self.remaining = [d.capacity_minutes for d in days]
        self.buffer_index = buffer_start_index(self.remaining)
        self.placed: dict[str, ScheduledTask] = {}
        self.unscheduled: dict[str, UnscheduledReason] = {}
        self.warnings: list[ScheduleWarning] = []

    def warn(
        self,
        code: WarningCode,
        level: WarningLevel,
        task_ids: tuple[str, ...] = (),
        dates: tuple[date, ...] = (),
    ) -> None:
        self.warnings.append(
            ScheduleWarning(code=code, level=level, task_ids=task_ids, dates=dates)
        )

    def place_pins(self, pinned: list[SchedulerTask]) -> None:
        """Pins consume capacity first and are kept as-is; every conflict only raises a warning."""
        pinned_minutes = [0] * len(self.days)
        pinned_ids: dict[int, list[str]] = defaultdict(list)
        for task in sorted(pinned, key=lambda t: t.id):
            overdue: list[date] = []
            outside: list[date] = []
            non_working: list[date] = []
            for alloc in task.pinned_allocations:
                i = self.index.get(alloc.date)
                if i is not None:
                    pinned_minutes[i] += alloc.minutes
                    pinned_ids[i].append(task.id)
                elif alloc.date < self.inp.quarter.start or alloc.date > self.window_end:
                    outside.append(alloc.date)
                elif alloc.date < self.window_start:
                    overdue.append(alloc.date)
                else:
                    non_working.append(alloc.date)
            conflicts: tuple[tuple[WarningCode, list[date]], ...] = (
                ("pinned_overdue", overdue),
                ("pinned_outside_quarter", outside),
                ("pinned_non_working_day", non_working),
            )
            for code, bad_dates in conflicts:
                if bad_dates:
                    self.warn(code, "red", (task.id,), tuple(bad_dates))
            self.placed[task.id] = ScheduledTask(
                task_id=task.id,
                start_date=task.pinned_allocations[0].date,
                end_date=task.pinned_allocations[-1].date,
                allocations=task.pinned_allocations,
                pinned=True,
                uses_buffer=False,
            )

        for i, minutes in enumerate(pinned_minutes):
            if minutes > self.remaining[i]:
                self.warn("pinned_over_capacity", "red", tuple(pinned_ids[i]), (self.dates[i],))
            self.remaining[i] = max(0, self.remaining[i] - minutes)

    def place(self, task: SchedulerTask) -> None:
        preds = [p for p in task.depends_on if p not in self.inp.done_task_ids]
        if any(p in self.unscheduled for p in preds):
            self.unscheduled[task.id] = "dependency_unscheduled"
            return

        earliest = self.window_start
        for pred in preds:
            earliest = max(earliest, self.placed[pred].end_date + ONE_DAY)

        left = task.estimate_minutes
        taken: list[tuple[int, int]] = []
        i = bisect_left(self.dates, earliest)
        while left > 0 and i < len(self.days):
            minutes = min(self.remaining[i], left)
            if minutes > 0:
                taken.append((i, minutes))
                left -= minutes
            i += 1
        if left > 0:
            self.unscheduled[task.id] = "exceeds_quarter"
            return

        for day_index, minutes in taken:
            self.remaining[day_index] -= minutes
        last_index = taken[-1][0]
        self.placed[task.id] = ScheduledTask(
            task_id=task.id,
            start_date=self.dates[taken[0][0]],
            end_date=self.dates[last_index],
            allocations=tuple(Allocation(date=self.dates[d], minutes=m) for d, m in taken),
            pinned=False,
            uses_buffer=self.buffer_index is not None and last_index >= self.buffer_index,
        )

    def check_pinned_dependencies(self, pinned: list[SchedulerTask]) -> None:
        for task in pinned:
            start = self.placed[task.id].start_date
            for pred in sorted(task.depends_on):
                if pred in self.inp.done_task_ids:
                    continue
                placed = self.placed.get(pred)
                if placed is None or placed.end_date >= start:
                    self.warn("pinned_dependency_conflict", "red", (pred, task.id))


def schedule(inp: ScheduleInput) -> ScheduleResult:
    """Place every unfinished task of the quarter; pure and deterministic for a given input.

    Raises ``ScheduleInputError`` for duplicate ids, unknown dependencies or cycles.
    """
    validate_references(inp.tasks, inp.done_task_ids)
    order = priority_topological_order(inp.tasks)

    window_start = max(inp.quarter.start, inp.today)
    days = working_days(window_start, inp.quarter.end, inp.calendar, inp.holidays)
    planner = _Planner(inp, days)
    supply = sum(planner.remaining)

    pinned = [task for task in order if task.is_pinned]
    planner.place_pins(pinned)
    for task in order:
        if not task.is_pinned:
            planner.place(task)
    planner.check_pinned_dependencies(pinned)

    by_id = {task.id: task for task in inp.tasks}
    buffer_ids = tuple(sorted(t for t, placed in planner.placed.items() if placed.uses_buffer))
    if buffer_ids:
        planner.warn("uses_buffer", "yellow", buffer_ids)
    reasons: tuple[UnscheduledReason, ...] = ("exceeds_quarter", "dependency_unscheduled")
    for reason in reasons:
        ids = tuple(sorted(t for t, r in planner.unscheduled.items() if r == reason))
        if ids:
            planner.warn(reason, "red", ids)

    warnings = tuple(sorted(planner.warnings, key=lambda w: (w.code, w.task_ids, w.dates)))
    status: FeasibilityStatus = "green"
    if any(w.level == "red" for w in warnings):
        status = "red"
    elif warnings:
        status = "yellow"

    late = sorted(planner.unscheduled)
    buffer_index = planner.buffer_index
    buffered_supply = sum(d.capacity_minutes for d in days[: buffer_index or 0])
    return ScheduleResult(
        window_start=window_start,
        window_end=inp.quarter.end,
        scheduled=tuple(
            sorted(planner.placed.values(), key=lambda s: (s.start_date, s.end_date, s.task_id))
        ),
        unscheduled=tuple(UnscheduledTask(task_id=t, reason=planner.unscheduled[t]) for t in late),
        warnings=warnings,
        feasibility=Feasibility(
            status=status,
            demand_minutes=sum(task.estimate_minutes for task in inp.tasks),
            supply_minutes=supply,
            buffered_supply_minutes=buffered_supply,
            buffer_start=None if buffer_index is None else days[buffer_index].date,
            late_task_ids=tuple(late),
            late_kr_ids=tuple(sorted({by_id[t].kr_id for t in late})),
            late_objective_ids=tuple(sorted({by_id[t].objective_id for t in late})),
        ),
    )
