"""Reschedule a whole quarter without the LLM (plan section 4.6).

Pins are never moved silently: every pin conflict is reported, and the new schedule is stored
only once each conflicting task has a resolution. A dry run computes the same result and rolls
back, so the preview and the applied schedule always match for unchanged data.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.schemas import (
    FeasibilityOut,
    PinConflict,
    PinConflictCode,
    RescheduleAction,
    TaskDateChange,
    UnscheduledTaskOut,
)
from app.api.views import feasibility_out
from app.persistence.models import Quarter, ScheduleRun, TaskDependency, TaskPin
from app.services.scheduling import (
    PlannedSchedule,
    latest_schedule,
    persist_schedule,
    plan_schedule,
)

Span = tuple[date, date, tuple[tuple[date, int], ...]]
_BASE_ACTIONS = [RescheduleAction.keep, RescheduleAction.unpin, RescheduleAction.repin]
_PIN_CODES = frozenset(code.value for code in PinConflictCode)


@dataclass(frozen=True)
class RescheduleOutcome:
    applied: bool
    run: ScheduleRun | None
    conflicts: list[PinConflict]
    unresolved_task_ids: list[int]
    changes: list[TaskDateChange]
    before: FeasibilityOut | None
    after: FeasibilityOut
    before_finish_date: date | None
    after_finish_date: date | None


def pin_conflicts(
    planned: PlannedSchedule, resolutions: dict[int, RescheduleAction]
) -> list[PinConflict]:
    pins = {
        int(t.id): {a.date: a.minutes for a in t.pinned_allocations}
        for t in planned.input.tasks
        if t.is_pinned
    }
    conflicts: list[PinConflict] = []
    for warning in planned.result.warnings:
        if warning.code not in _PIN_CODES:
            continue
        code = PinConflictCode(warning.code)
        ids = [int(t) for t in warning.task_ids]
        if code == PinConflictCode.pinned_dependency_conflict:
            pred, task_id = ids
            start = min(pins[task_id])
            conflicts.append(_conflict(task_id, code, [start], [pred], None, None, resolutions))
        elif code == PinConflictCode.pinned_over_capacity:
            day = warning.dates[0]
            pinned = sum(pins[t].get(day, 0) for t in ids)
            capacity = planned.calendar.capacity(day)
            for task_id in ids:
                others = [t for t in ids if t != task_id]
                conflicts.append(
                    _conflict(task_id, code, [day], others, capacity, pinned, resolutions)
                )
        else:
            for task_id in ids:
                conflicts.append(
                    _conflict(task_id, code, list(warning.dates), [], None, None, resolutions)
                )
    return sorted(conflicts, key=lambda c: (c.task_id, c.code.value, c.dates))


def _conflict(
    task_id: int,
    code: PinConflictCode,
    dates: list[date],
    related: list[int],
    capacity: int | None,
    pinned: int | None,
    resolutions: dict[int, RescheduleAction],
) -> PinConflict:
    allowed = list(_BASE_ACTIONS)
    if code == PinConflictCode.pinned_dependency_conflict:
        allowed.append(RescheduleAction.unlink)
    return PinConflict(
        task_id=task_id,
        code=code,
        dates=dates,
        related_task_ids=sorted(related),
        capacity_minutes=capacity,
        pinned_minutes=pinned,
        allowed_actions=allowed,
        resolution=resolutions.get(task_id),
    )


def _spans_from_run(run: ScheduleRun | None) -> dict[int, Span]:
    days: dict[int, list[tuple[date, int]]] = {}
    if run is not None:
        for a in run.allocations:
            if not a.done:
                days.setdefault(a.task_id, []).append((a.date, a.minutes))
    return {t: (min(d)[0], max(d)[0], tuple(sorted(d))) for t, d in days.items()}


def _spans_from_plan(planned: PlannedSchedule) -> dict[int, Span]:
    return {
        int(s.task_id): (
            s.start_date,
            s.end_date,
            tuple((a.date, a.minutes) for a in s.allocations),
        )
        for s in planned.result.scheduled
    }


def _changes(
    before: dict[int, Span], after: dict[int, Span], known: set[int]
) -> list[TaskDateChange]:
    changes = []
    for task_id in sorted((before.keys() | after.keys()) & known):
        old, new = before.get(task_id), after.get(task_id)
        if old == new:
            continue
        changes.append(
            TaskDateChange(
                task_id=task_id,
                before_start=old[0] if old else None,
                before_end=old[1] if old else None,
                after_start=new[0] if new else None,
                after_end=new[1] if new else None,
            )
        )
    return changes


def _finish(spans: dict[int, Span]) -> date | None:
    return max((span[1] for span in spans.values()), default=None)


def _unlink(
    session: Session, conflicts: list[PinConflict], actions: dict[int, RescheduleAction]
) -> None:
    for conflict in conflicts:
        if (
            conflict.code == PinConflictCode.pinned_dependency_conflict
            and actions.get(conflict.task_id) == RescheduleAction.unlink
        ):
            session.execute(
                delete(TaskDependency).where(
                    TaskDependency.task_id == conflict.task_id,
                    TaskDependency.depends_on_id.in_(conflict.related_task_ids),
                )
            )


def _store_pins(
    session: Session, planned: PlannedSchedule, unpin: set[int], repin: set[int]
) -> None:
    placed = {int(s.task_id): s for s in planned.result.scheduled}
    changed = [t for t in planned.tasks if t.id in unpin | repin]
    for task in changed:
        task.pins.clear()
        task.pinned = False
    # Old rows must be gone before new ones reuse the same (task, date) keys.
    session.flush()
    for task in changed:
        if task.id in repin and task.id in placed:
            task.pins.extend(
                TaskPin(date=a.date, minutes=a.minutes) for a in placed[task.id].allocations
            )
            task.pinned = True


def reschedule(
    session: Session,
    quarter: Quarter,
    today: date,
    resolutions: dict[int, RescheduleAction],
    *,
    dry_run: bool,
) -> RescheduleOutcome:
    """Commits when the schedule is applied and rolls back otherwise.

    Raises ``ScheduleInputError`` when stored dependencies are inconsistent.
    """
    previous = latest_schedule(session, quarter.id)
    before_spans = _spans_from_run(previous)
    initial = plan_schedule(session, quarter, today)
    owners = {t.id: (t.key_result_id, t.key_result.objective_id) for t in initial.tasks}
    pinned_ids = {int(t.id) for t in initial.input.tasks if t.is_pinned}
    before = None
    if previous is not None:
        before_late = [
            UnscheduledTaskOut(
                task_id=u["task_id"],
                key_result_id=owners[u["task_id"]][0],
                objective_id=owners[u["task_id"]][1],
                reason=u["reason"],
            )
            for u in previous.unscheduled
            if u["task_id"] in owners
        ]
        before = feasibility_out(
            previous.status,
            previous.demand_minutes,
            previous.supply_minutes,
            previous.buffered_supply_minutes,
            previous.buffer_start,
            before_late,
        )

    _unlink(session, pin_conflicts(initial, resolutions), resolutions)
    unpin = {t for t, a in resolutions.items() if a == RescheduleAction.unpin and t in pinned_ids}
    repin = {t for t, a in resolutions.items() if a == RescheduleAction.repin and t in pinned_ids}
    session.flush()
    session.expire_all()
    final = plan_schedule(session, quarter, today, frozenset(unpin | repin))
    conflicts = pin_conflicts(final, resolutions)
    unresolved = sorted({c.task_id for c in conflicts if c.resolution is None})
    applied = not dry_run and not unresolved

    run = None
    if applied:
        _store_pins(session, final, unpin, repin)
        session.flush()
        session.expire_all()
        final = plan_schedule(session, quarter, today)
        run = persist_schedule(session, final, plan_run_id=None)

    after_spans = _spans_from_plan(final)
    result = final.result
    after = feasibility_out(
        result.feasibility.status,
        result.feasibility.demand_minutes,
        result.feasibility.supply_minutes,
        result.feasibility.buffered_supply_minutes,
        result.feasibility.buffer_start,
        [
            UnscheduledTaskOut(
                task_id=int(u.task_id),
                key_result_id=owners[int(u.task_id)][0],
                objective_id=owners[int(u.task_id)][1],
                reason=u.reason,
            )
            for u in result.unscheduled
        ],
    )
    outcome = RescheduleOutcome(
        applied=applied,
        run=run,
        conflicts=conflicts,
        unresolved_task_ids=unresolved,
        changes=_changes(before_spans, after_spans, set(owners)),
        before=before,
        after=after,
        before_finish_date=_finish(before_spans),
        after_finish_date=_finish(after_spans),
    )
    if applied:
        session.commit()
    else:
        session.rollback()
    return outcome
