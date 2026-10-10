"""Build scheduler input from the database and persist the result as a ``ScheduleRun``."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.calendar import day_capacity_minutes
from app.domain.calendar_config import DEFAULT_WORKDAY_MINUTES, CalendarConfig
from app.domain.quarter import Quarter as QuarterPeriod
from app.persistence.models import (
    Allocation,
    CalendarSettings,
    Holiday,
    KeyResult,
    LeaveDay,
    Objective,
    Quarter,
    ScheduleRun,
    Task,
)
from app.scheduler import Allocation as PinnedAllocation
from app.scheduler import ScheduleInput, ScheduleResult, SchedulerTask, schedule
from app.scheduler.engine import ONE_DAY

MAKEUP_KIND = "makeup_day"
WEEKDAY_COLUMNS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
# Objectives are scheduled strictly by priority, then by their position in the form.
_POSITION_SLOTS = 10_000


def period(quarter: Quarter) -> QuarterPeriod:
    return QuarterPeriod(year=quarter.year, number=quarter.number)


def effective_today(quarter: Quarter, today: date) -> date:
    """The first day tasks may start: the quarter's plan start when it is later than today."""
    return max(today, quarter.plan_start) if quarter.plan_start else today


def global_calendar(session: Session) -> CalendarSettings:
    row = session.scalars(
        select(CalendarSettings)
        .where(CalendarSettings.quarter_id.is_(None))
        .order_by(CalendarSettings.id)
    ).first()
    if row is None:
        defaults = CalendarConfig()
        row = CalendarSettings(
            quarter_id=None,
            work_saturday=defaults.work_saturday,
            work_sunday=defaults.work_sunday,
            work_holidays=defaults.work_holidays,
            **{
                f"{day}_minutes": minutes
                for day, minutes in zip(
                    WEEKDAY_COLUMNS, defaults.weekday_capacity_minutes, strict=True
                )
            },
        )
        session.add(row)
        session.flush()
    return row


def effective_calendar(session: Session, quarter_id: int) -> CalendarSettings:
    override = session.scalars(
        select(CalendarSettings).where(CalendarSettings.quarter_id == quarter_id)
    ).first()
    return override or global_calendar(session)


def weekday_minutes(row: CalendarSettings) -> tuple[int, int, int, int, int, int, int]:
    return (
        row.mon_minutes,
        row.tue_minutes,
        row.wed_minutes,
        row.thu_minutes,
        row.fri_minutes,
        row.sat_minutes,
        row.sun_minutes,
    )


class CalendarInputs:
    """Effective calendar of one quarter; ``quarter`` may be a period nobody planned yet."""

    def __init__(self, session: Session, quarter: Quarter | QuarterPeriod) -> None:
        quarter_id: int | None
        if isinstance(quarter, Quarter):
            span, quarter_id = period(quarter), quarter.id
        else:
            span = quarter
            quarter_id = session.scalar(
                select(Quarter.id).where(Quarter.year == span.year, Quarter.number == span.number)
            )
        self.span = span
        in_quarter = (Holiday.date >= span.start) & (Holiday.date <= span.end)
        rows = session.scalars(select(Holiday).where(in_quarter)).all()
        self.holidays = frozenset(h.date for h in rows if h.kind != MAKEUP_KIND)
        self.leave_days = frozenset(
            session.scalars(
                select(LeaveDay.date).where(
                    (LeaveDay.date >= span.start) & (LeaveDay.date <= span.end)
                )
            ).all()
        )
        makeup_days = frozenset(h.date for h in rows if h.kind == MAKEUP_KIND) - self.leave_days
        settings = (
            global_calendar(session)
            if quarter_id is None
            else effective_calendar(session, quarter_id)
        )
        weekdays = weekday_minutes(settings)
        self.config = CalendarConfig(
            weekday_capacity_minutes=weekdays,
            work_saturday=settings.work_saturday,
            work_sunday=settings.work_sunday,
            work_holidays=settings.work_holidays,
            leave_days=self.leave_days,
            makeup_days=makeup_days,
            makeup_day_capacity_minutes=max(weekdays[:5]) or DEFAULT_WORKDAY_MINUTES,
        )

    def capacity(self, day: date) -> int:
        return day_capacity_minutes(day, self.config, self.holidays)


class PinError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def fill_pin_days(start: date, minutes: int, calendar: CalendarInputs) -> list[tuple[date, int]]:
    """Days for a task moved to ``start``: full day capacities from ``start`` onwards.

    Other tasks' load is ignored on purpose: a pin wins, and an overfull day is reported as a
    conflict when the quarter is rescheduled. Raises ``PinError``.
    """
    if not calendar.span.start <= start <= calendar.span.end:
        raise PinError("pin_outside_quarter", f"{start} is outside the quarter")
    if calendar.capacity(start) == 0:
        raise PinError("pin_non_working_day", f"{start} is not a working day")
    days: list[tuple[date, int]] = []
    day, left = start, minutes
    while left > 0 and day <= calendar.span.end:
        take = min(calendar.capacity(day), left)
        if take > 0:
            days.append((day, take))
            left -= take
        day += ONE_DAY
    if left > 0:
        raise PinError(
            "pin_exceeds_quarter", f"{minutes} minutes from {start} pass the quarter end"
        )
    return days


def check_pin_days(days: list[tuple[date, int]], minutes: int, calendar: CalendarInputs) -> None:
    """Explicit pins: inside the quarter, on working days, and covering the estimate exactly."""
    dates = [d for d, _ in days]
    if len(dates) != len(set(dates)):
        raise PinError("pin_duplicate_date", "a date is pinned more than once")
    if sum(m for _, m in days) != minutes:
        raise PinError("pin_minutes_mismatch", f"pinned minutes must add up to {minutes}")
    for day, _ in days:
        if not calendar.span.start <= day <= calendar.span.end:
            raise PinError("pin_outside_quarter", f"{day} is outside the quarter")
        if calendar.capacity(day) == 0:
            raise PinError("pin_non_working_day", f"{day} is not a working day")


def quarter_tasks(session: Session, quarter_id: int) -> list[Task]:
    return list(
        session.scalars(
            select(Task)
            .join(Task.key_result)
            .join(KeyResult.objective)
            .where(Objective.quarter_id == quarter_id)
            .options(
                selectinload(Task.dependencies),
                selectinload(Task.pins),
                selectinload(Task.key_result).selectinload(KeyResult.objective),
            )
            .order_by(Task.id)
        ).all()
    )


def latest_schedule(session: Session, quarter_id: int) -> ScheduleRun | None:
    return session.scalars(
        select(ScheduleRun)
        .where(ScheduleRun.quarter_id == quarter_id)
        .order_by(ScheduleRun.id.desc())
        .limit(1)
    ).first()


def pinned_days(task: Task) -> tuple[PinnedAllocation, ...]:
    """Stored pins; a pin that no longer covers the estimate is ignored rather than trusted."""
    pins = task.pinned_allocations
    if not pins or sum(p.minutes for p in pins) != task.estimate_minutes:
        return ()
    return tuple(PinnedAllocation(date=p.date, minutes=p.minutes) for p in pins)


def is_schedulable(task: Task) -> bool:
    return task.status != "done" and task.key_result.active and task.key_result.objective.active


def build_input(
    quarter: Quarter,
    today: date,
    tasks: list[Task],
    calendar: CalendarInputs,
    unpinned: frozenset[int] = frozenset(),
) -> ScheduleInput:
    """Unfinished tasks of active KRs and objectives; ``unpinned`` tasks are placed as if not
    pinned.

    Dependencies on finished tasks or on tasks of inactive KRs/objectives count as satisfied.
    """
    scheduler_tasks = []
    satisfied_ids = []
    for task in tasks:
        if not is_schedulable(task):
            satisfied_ids.append(str(task.id))
            continue
        objective = task.key_result.objective
        scheduler_tasks.append(
            SchedulerTask(
                id=str(task.id),
                objective_id=str(objective.id),
                kr_id=str(task.key_result_id),
                estimate_minutes=task.estimate_minutes,
                objective_priority=PRIORITY_RANK[objective.priority] * _POSITION_SLOTS
                + objective.position,
                kr_order=task.key_result.position,
                task_order=task.position,
                depends_on=frozenset(str(d) for d in task.depends_on),
                pinned_allocations=() if task.id in unpinned else pinned_days(task),
            )
        )
    return ScheduleInput(
        quarter=period(quarter),
        today=today,
        plan_start=quarter.plan_start,
        calendar=calendar.config,
        holidays=calendar.holidays,
        tasks=tuple(scheduler_tasks),
        done_task_ids=frozenset(satisfied_ids),
    )


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        items = [_canonical(v) for v in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


def input_fingerprint(inp: ScheduleInput) -> str:
    """Stable across processes (sets are sorted) and blind to ``today``, so that time passing
    alone never marks a schedule as stale."""
    data = _canonical(inp.model_dump(exclude={"today"}))
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PlannedSchedule:
    """A scheduler run that is not stored yet, so it can be previewed or discarded."""

    quarter: Quarter
    today: date
    tasks: list[Task]
    calendar: CalendarInputs
    input: ScheduleInput
    result: ScheduleResult

    @property
    def fingerprint(self) -> str:
        return input_fingerprint(self.input)


def plan_schedule(
    session: Session, quarter: Quarter, today: date, unpinned: frozenset[int] = frozenset()
) -> PlannedSchedule:
    """Raises ``ScheduleInputError`` when stored dependencies are inconsistent."""
    today = effective_today(quarter, today)
    tasks = quarter_tasks(session, quarter.id)
    calendar = CalendarInputs(session, quarter)
    inp = build_input(quarter, today, tasks, calendar, unpinned)
    return PlannedSchedule(quarter, today, tasks, calendar, inp, schedule(inp))


def is_stale(session: Session, run: ScheduleRun, today: date) -> bool:
    quarter = session.get_one(Quarter, run.quarter_id)
    today = effective_today(quarter, today)
    tasks = quarter_tasks(session, quarter.id)
    current = input_fingerprint(
        build_input(quarter, today, tasks, CalendarInputs(session, quarter))
    )
    return run.input_hash != current


def _days(
    result: ScheduleResult, calendar: CalendarInputs, scheduled_minutes: dict[date, int]
) -> list[dict[str, Any]]:
    days: list[dict[str, Any]] = []
    day = result.window_start
    buffer_start = result.feasibility.buffer_start
    while day <= result.window_end:
        capacity = day_capacity_minutes(day, calendar.config, calendar.holidays)
        off_reason: str | None = None
        if capacity == 0:
            if day in calendar.leave_days:
                off_reason = "leave"
            elif (day.weekday() == 5 and not calendar.config.work_saturday) or (
                day.weekday() == 6 and not calendar.config.work_sunday
            ):
                off_reason = "weekend"
            elif day in calendar.holidays and not calendar.config.work_holidays:
                off_reason = "holiday"
            else:
                off_reason = "no_capacity"
        days.append(
            {
                "date": day.isoformat(),
                "capacity_minutes": capacity,
                "scheduled_minutes": scheduled_minutes.get(day, 0),
                "is_buffer": capacity > 0 and buffer_start is not None and day >= buffer_start,
                "off_reason": off_reason,
            }
        )
        day += timedelta(days=1)
    return days


def _done_history(
    session: Session, planned: PlannedSchedule, window_start: date
) -> list[Allocation]:
    """Past days of finished tasks from the previous run; they never consume capacity again."""
    previous = latest_schedule(session, planned.quarter.id)
    if previous is None:
        return []
    done_ids = {t.id for t in planned.tasks if t.status == "done"}
    return [
        Allocation(
            task_id=a.task_id,
            date=a.date,
            minutes=a.minutes,
            pinned=False,
            uses_buffer=False,
            done=True,
        )
        for a in previous.allocations
        if a.task_id in done_ids and a.date < window_start
    ]


def persist_schedule(
    session: Session, planned: PlannedSchedule, plan_run_id: str | None
) -> ScheduleRun:
    """Store ``planned`` as the quarter's latest schedule; the caller commits."""
    result = planned.result
    scheduled_minutes: dict[date, int] = {}
    allocations = _done_history(session, planned, result.window_start)
    for placed in result.scheduled:
        for alloc in placed.allocations:
            scheduled_minutes[alloc.date] = scheduled_minutes.get(alloc.date, 0) + alloc.minutes
            allocations.append(
                Allocation(
                    task_id=int(placed.task_id),
                    date=alloc.date,
                    minutes=alloc.minutes,
                    pinned=placed.pinned,
                    uses_buffer=placed.uses_buffer,
                )
            )

    feasibility = result.feasibility
    run = ScheduleRun(
        quarter_id=planned.quarter.id,
        plan_run_id=plan_run_id,
        today=planned.today,
        window_start=result.window_start,
        window_end=result.window_end,
        status=feasibility.status,
        demand_minutes=feasibility.demand_minutes,
        supply_minutes=feasibility.supply_minutes,
        buffered_supply_minutes=feasibility.buffered_supply_minutes,
        buffer_start=feasibility.buffer_start,
        input_hash=planned.fingerprint,
        warnings=[
            {
                "code": w.code,
                "level": w.level,
                "task_ids": [int(t) for t in w.task_ids],
                "dates": [d.isoformat() for d in w.dates],
            }
            for w in result.warnings
        ],
        unscheduled=[{"task_id": int(u.task_id), "reason": u.reason} for u in result.unscheduled],
        days=_days(result, planned.calendar, scheduled_minutes),
        allocations=allocations,
    )
    session.add(run)
    session.flush()
    return run


def create_schedule_run(
    session: Session, quarter: Quarter, today: date, plan_run_id: str | None
) -> ScheduleRun:
    """Schedule every unfinished task of the quarter's active objectives; the caller commits.

    Raises ``ScheduleInputError`` when stored dependencies are inconsistent.
    """
    return persist_schedule(session, plan_schedule(session, quarter, today), plan_run_id)
