"""Overload options: list and evaluate what-if variants, apply them in one transaction, undo.

Evaluating never writes. Applying changes the quarter's own calendar override (never the global
settings), drops KRs or pauses objectives through their ``active`` flag, moves deferred KRs to
the next quarter, then stores a fresh schedule. ``OptionApplication.snapshot`` keeps what undo
restores.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import (
    CalendarSettings,
    OptionEffect,
    OptionEffectCode,
    OptionEvaluation,
    OptionGroup,
    OptionOutcome,
    OverloadOption,
    OverloadOptions,
    UnscheduledTaskOut,
    WeekdayCapacity,
    WeekdayHint,
)
from app.api.schemas import OptionKind as ApiOptionKind
from app.api.views import feasibility_out
from app.domain.calendar_config import CalendarConfig
from app.domain.quarter import Quarter as QuarterPeriod
from app.persistence.models import CalendarSettings as CalendarRow
from app.persistence.models import (
    KeyResult,
    Objective,
    OptionApplication,
    Quarter,
    Task,
    TaskDependency,
    TaskPin,
    utcnow,
)
from app.scheduler import ScheduleInput, ScheduleResult, schedule
from app.scheduler.whatif import (
    CALENDAR_KINDS,
    WEEKDAY_STEP_MINUTES,
    Measures,
    Option,
    OptionError,
    OptionKind,
    apply_options,
    canonical,
    conflicting_pairs,
    green,
    measure,
    min_weekday_extra,
    not_red,
    parse_option,
)
from app.services.scheduling import (
    WEEKDAY_COLUMNS,
    PlannedSchedule,
    persist_schedule,
    plan_schedule,
    weekday_minutes,
)

DEFAULT_EXTRA_MINUTES = 60
_GROUPS = {
    OptionKind.weekday_minutes: OptionGroup.more_time,
    OptionKind.work_saturday: OptionGroup.more_time,
    OptionKind.work_sunday: OptionGroup.more_time,
    OptionKind.work_holidays: OptionGroup.more_time,
    OptionKind.drop_kr: OptionGroup.less_scope,
    OptionKind.drop_objective: OptionGroup.less_scope,
    OptionKind.defer_kr: OptionGroup.defer,
}
Owners = dict[int, tuple[int, int]]


class StateConflict(OptionError):
    """The request is valid but clashes with stored state (HTTP 409)."""


@dataclass(frozen=True)
class WhatIf:
    quarter: Quarter
    planned: PlannedSchedule
    owners: Owners
    kr_objectives: dict[str, str]
    objectives: frozenset[str]
    base: Measures

    @property
    def input(self) -> ScheduleInput:
        return self.planned.input


def _owners(planned: PlannedSchedule) -> Owners:
    return {t.id: (t.key_result_id, t.key_result.objective_id) for t in planned.tasks}


def load(session: Session, quarter: Quarter, today: date) -> WhatIf:
    """Raises ``ScheduleInputError`` when stored dependencies are inconsistent."""
    planned = plan_schedule(session, quarter, today)
    kr_objectives = {
        str(kr.id): str(objective.id)
        for objective in quarter.objectives
        if objective.active
        for kr in objective.key_results
        if kr.active
    }
    return WhatIf(
        quarter=quarter,
        planned=planned,
        owners=_owners(planned),
        kr_objectives=kr_objectives,
        objectives=frozenset(str(o.id) for o in quarter.objectives if o.active),
        base=measure(planned.input, planned.result),
    )


def outcome(
    owners: Owners, base: Measures, inp: ScheduleInput, result: ScheduleResult
) -> OptionOutcome:
    measures = measure(inp, result)
    feasibility = result.feasibility
    late = [
        UnscheduledTaskOut(
            task_id=int(u.task_id),
            key_result_id=owners[int(u.task_id)][0],
            objective_id=owners[int(u.task_id)][1],
            reason=u.reason,
        )
        for u in result.unscheduled
    ]
    return OptionOutcome(
        feasibility=feasibility_out(
            feasibility.status,
            feasibility.demand_minutes,
            feasibility.supply_minutes,
            feasibility.buffered_supply_minutes,
            feasibility.buffer_start,
            late,
        ),
        finish_date=measures.finish_date,
        late_task_count=measures.late_task_count,
        shortfall_minutes=measures.shortfall_minutes,
        buffer_minutes=measures.buffer_minutes,
        buffer_used_minutes=measures.buffer_used_minutes,
        supply_delta_minutes=measures.supply_minutes - base.supply_minutes,
        demand_delta_minutes=measures.demand_minutes - base.demand_minutes,
        resolves_overload=not_red(result),
    )


def _outcome_of(w: WhatIf, options: list[Option]) -> OptionOutcome:
    inp = apply_options(w.input, options)
    return outcome(w.owners, w.base, inp, schedule(inp))


def _not_applicable(option: Option, reason: str) -> OptionError:
    return OptionError("option_not_applicable", f"{option.id}: {reason}")


def _check_applicable(w: WhatIf, option: Option) -> None:
    calendar = w.input.calendar
    weekdays = calendar.weekday_capacity_minutes
    if option.kind == OptionKind.weekday_minutes:
        working = [m for m in weekdays[:5] if m > 0]
        if not working or apply_options(w.input, [option]).calendar == calendar:
            raise _not_applicable(option, "working weekdays are already at the maximum")
    elif option.kind == OptionKind.work_saturday:
        if calendar.work_saturday and weekdays[5] > 0:
            raise _not_applicable(option, "Saturdays are already working days")
    elif option.kind == OptionKind.work_sunday:
        if calendar.work_sunday and weekdays[6] > 0:
            raise _not_applicable(option, "Sundays are already working days")
    elif option.kind == OptionKind.work_holidays:
        if calendar.work_holidays:
            raise _not_applicable(option, "holidays are already working days")
    elif option.kind == OptionKind.drop_objective:
        if option.target not in w.objectives:
            raise _not_applicable(option, "not an active objective of this quarter")
    elif option.target not in w.kr_objectives:
        raise _not_applicable(option, "not an active key result of this quarter")


def select_options(w: WhatIf, option_ids: list[str]) -> list[Option]:
    """Parsed, applicable and conflict-free options; raises ``OptionError``."""
    options = canonical(parse_option(option_id) for option_id in option_ids)
    for option in options:
        _check_applicable(w, option)
    pairs = conflicting_pairs(options, w.kr_objectives)
    if pairs:
        described = "; ".join(f"{a.id} excludes {b.id}" for a, b in pairs)
        raise OptionError("options_conflict", described)
    return options


def next_period(quarter: Quarter) -> QuarterPeriod:
    if quarter.number == 4:
        return QuarterPeriod(year=quarter.year + 1, number=1)
    return QuarterPeriod(year=quarter.year, number=quarter.number + 1)


def _calendar_schema(config: CalendarConfig) -> CalendarSettings:
    minutes = dict(zip(WEEKDAY_COLUMNS, config.weekday_capacity_minutes, strict=True))
    return CalendarSettings(
        capacity_minutes=WeekdayCapacity(**minutes),
        work_saturday=config.work_saturday,
        work_sunday=config.work_sunday,
        work_holidays=config.work_holidays,
    )


def _effect(option: Option, code: OptionEffectCode, **fields: Any) -> OptionEffect:
    values: dict[str, Any] = {
        "key_result_id": None,
        "objective_id": None,
        "task_count": 0,
        "pinned_task_ids": [],
        "calendar": None,
        "target_year": None,
        "target_number": None,
        "target_quarter_exists": None,
    }
    values.update(fields)
    return OptionEffect(option_id=option.id, code=code, **values)


def effects(session: Session, w: WhatIf, options: list[Option]) -> list[OptionEffect]:
    calendar_options = [o for o in options if o.kind in CALENDAR_KINDS]
    new_calendar = None
    if calendar_options:
        new_calendar = _calendar_schema(apply_options(w.input, calendar_options).calendar)
    target = next_period(w.quarter)
    target_exists = (
        session.scalar(
            select(Quarter.id).where(Quarter.year == target.year, Quarter.number == target.number)
        )
        is not None
    )
    result = []
    for option in options:
        if option.kind in CALENDAR_KINDS:
            result.append(
                _effect(option, OptionEffectCode.quarter_calendar_changed, calendar=new_calendar)
            )
            continue
        if option.kind == OptionKind.drop_objective:
            tasks = [t for t in w.input.tasks if t.objective_id == option.target]
            result.append(
                _effect(
                    option,
                    OptionEffectCode.objective_paused,
                    objective_id=int(option.target),
                    task_count=len(tasks),
                )
            )
            continue
        tasks = [t for t in w.input.tasks if t.kr_id == option.target]
        common = {
            "key_result_id": int(option.target),
            "objective_id": int(w.kr_objectives[option.target]),
            "task_count": len(tasks),
        }
        if option.kind == OptionKind.drop_kr:
            result.append(_effect(option, OptionEffectCode.key_result_dropped, **common))
        else:
            result.append(
                _effect(
                    option,
                    OptionEffectCode.key_result_deferred,
                    pinned_task_ids=sorted(int(t.id) for t in tasks if t.is_pinned),
                    target_year=target.year,
                    target_number=target.number,
                    target_quarter_exists=target_exists,
                    **common,
                )
            )
    return result


# --- listing and evaluation -----------------------------------------------------------------


def _kr_rank(w: WhatIf) -> dict[str, tuple[int, int, int]]:
    """Scheduling priority per KR (larger = lower priority)."""
    ranks: dict[str, tuple[int, int, int]] = {}
    for task in w.input.tasks:
        ranks.setdefault(task.kr_id, (task.objective_priority, task.kr_order, int(task.kr_id)))
    return ranks


def _candidates(w: WhatIf) -> list[Option]:
    candidates = [
        Option(OptionKind.weekday_minutes, minutes=DEFAULT_EXTRA_MINUTES),
        Option(OptionKind.work_saturday),
        Option(OptionKind.work_sunday),
        Option(OptionKind.work_holidays),
    ]
    options = []
    for option in candidates:
        try:
            _check_applicable(w, option)
        except OptionError:
            continue
        options.append(option)

    ranks = _kr_rank(w)
    late_krs = sorted(w.planned.result.feasibility.late_kr_ids, key=lambda kr: ranks[kr])
    if late_krs:
        lowest = late_krs[-1]
        options.append(Option(OptionKind.drop_kr, target=lowest))
        objective_rank = {
            t.objective_id: (t.objective_priority, int(t.objective_id)) for t in w.input.tasks
        }
        late_objectives = sorted(
            w.planned.result.feasibility.late_objective_ids, key=lambda o: objective_rank[o]
        )
        options.append(Option(OptionKind.drop_objective, target=late_objectives[-1]))
        options.extend(Option(OptionKind.defer_kr, target=kr) for kr in late_krs)
    return options


def _targets(w: WhatIf, option: Option) -> tuple[int | None, int | None]:
    """(key result, objective) an option acts on."""
    if option.kind == OptionKind.drop_objective:
        return None, int(option.target)
    if option.target:
        return int(option.target), int(w.kr_objectives[option.target])
    return None, None


def _listed(session: Session, w: WhatIf, option: Option, result: OptionOutcome) -> OverloadOption:
    key_result_id, objective_id = _targets(w, option)
    return OverloadOption(
        id=option.id,
        kind=ApiOptionKind(option.kind.value),
        group=_GROUPS[option.kind],
        extra_minutes=option.minutes or None,
        key_result_id=key_result_id,
        objective_id=objective_id,
        outcome=result,
        conflicts_with=[],
        effects=effects(session, w, [option]),
    )


def list_options(session: Session, quarter: Quarter, today: date) -> OverloadOptions:
    """Every option on its own, each backed by one scheduler run on the current data."""
    w = load(session, quarter, today)
    current = outcome(w.owners, w.base, w.input, w.planned.result)
    listed: list[tuple[Option, OverloadOption]] = []
    for option in _candidates(w):
        result = _outcome_of(w, [option])
        if option.kind in CALENDAR_KINDS and result.supply_delta_minutes <= 0:
            continue
        listed.append((option, _listed(session, w, option, result)))
    options = []
    for option, item in listed:
        conflicts = [
            other.id for other, _ in listed if conflicting_pairs([option, other], w.kr_objectives)
        ]
        options.append(item.model_copy(update={"conflicts_with": conflicts}))

    hint = None
    if any(o.kind == OptionKind.weekday_minutes for o, _ in listed):
        enough = min_weekday_extra(w.input, not_red)
        best = min_weekday_extra(w.input, green)
        hint = WeekdayHint(
            current_minutes=list(w.input.calendar.weekday_capacity_minutes[:5]),
            step_minutes=WEEKDAY_STEP_MINUTES,
            min_extra_minutes_not_red=enough.minutes if enough else None,
            min_extra_minutes_green=best.minutes if best else None,
        )
    return OverloadOptions(
        quarter_id=quarter.id,
        overloaded=not current.resolves_overload,
        current=current,
        options=options,
        weekday_hint=hint,
    )


def evaluate(
    session: Session, quarter: Quarter, today: date, option_ids: list[str]
) -> OptionEvaluation:
    """Raises ``OptionError`` for unknown, inapplicable or conflicting options."""
    w = load(session, quarter, today)
    options = select_options(w, option_ids)
    return OptionEvaluation(
        option_ids=[o.id for o in options],
        before=outcome(w.owners, w.base, w.input, w.planned.result),
        after=_outcome_of(w, options),
        effects=effects(session, w, options),
    )


# --- apply and undo -------------------------------------------------------------------------


def _request_hash(quarter_id: int, option_ids: list[str]) -> str:
    payload = json.dumps({"quarter_id": quarter_id, "option_ids": option_ids}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _by_key(session: Session, key: str) -> OptionApplication | None:
    return session.scalars(
        select(OptionApplication).where(OptionApplication.idempotency_key == key)
    ).first()


def _replay(existing: OptionApplication, quarter_id: int, request_hash: str) -> OptionApplication:
    if existing.quarter_id != quarter_id or existing.request_hash != request_hash:
        raise StateConflict(
            "idempotency_key_reused", "this Idempotency-Key was used for a different request"
        )
    return existing


def _override(session: Session, quarter_id: int) -> CalendarRow | None:
    return session.scalars(select(CalendarRow).where(CalendarRow.quarter_id == quarter_id)).first()


def _row_values(row: CalendarRow) -> dict[str, Any]:
    values: dict[str, Any] = dict(
        zip((f"{d}_minutes" for d in WEEKDAY_COLUMNS), weekday_minutes(row), strict=True)
    )
    values.update(
        work_saturday=row.work_saturday,
        work_sunday=row.work_sunday,
        work_holidays=row.work_holidays,
    )
    return values


def _config_values(config: CalendarConfig) -> dict[str, Any]:
    values: dict[str, Any] = dict(
        zip(
            (f"{d}_minutes" for d in WEEKDAY_COLUMNS),
            config.weekday_capacity_minutes,
            strict=True,
        )
    )
    values.update(
        work_saturday=config.work_saturday,
        work_sunday=config.work_sunday,
        work_holidays=config.work_holidays,
    )
    return values


def _write_override(session: Session, quarter_id: int, values: dict[str, Any] | None) -> None:
    row = _override(session, quarter_id)
    if values is None:
        if row is not None:
            session.delete(row)
        return
    if row is None:
        row = CalendarRow(quarter_id=quarter_id)
        session.add(row)
    for field, value in values.items():
        setattr(row, field, value)


def _next_position(session: Session, column: Any, parent_filter: Any) -> int:
    current = session.scalar(select(func.max(column)).where(parent_filter))
    return 0 if current is None else int(current) + 1


def _defer(session: Session, quarter: Quarter, kr: KeyResult) -> dict[str, Any]:
    """Moves ``kr`` with all its tasks under an objective of the next quarter.

    Dependencies crossing the KR boundary and the pins of its tasks (dates of this quarter)
    are removed; both are recorded for undo.
    """
    target_period = next_period(quarter)
    target = session.scalars(
        select(Quarter).where(
            Quarter.year == target_period.year, Quarter.number == target_period.number
        )
    ).first()
    created_quarter_id = None
    if target is None:
        target = Quarter(year=target_period.year, number=target_period.number)
        session.add(target)
        session.flush()
        created_quarter_id = target.id

    source = kr.objective
    objective = session.scalars(
        select(Objective)
        .where(Objective.quarter_id == target.id, Objective.title == source.title)
        .order_by(Objective.id)
    ).first()
    created_objective = objective is None
    if objective is None:
        objective = Objective(
            quarter_id=target.id,
            title=source.title,
            priority=source.priority,
            position=_next_position(session, Objective.position, Objective.quarter_id == target.id),
            active=True,
        )
        session.add(objective)
        session.flush()

    task_ids = list(session.scalars(select(Task.id).where(Task.key_result_id == kr.id)).all())
    inside_task = TaskDependency.task_id.in_(task_ids)
    inside_dep = TaskDependency.depends_on_id.in_(task_ids)
    crossing = list(
        session.scalars(
            select(TaskDependency).where(
                or_(and_(inside_task, ~inside_dep), and_(~inside_task, inside_dep))
            )
        ).all()
    )
    dependencies = sorted([d.task_id, d.depends_on_id] for d in crossing)
    for edge in crossing:
        session.delete(edge)

    pins: list[dict[str, Any]] = []
    for task in kr.tasks:
        if task.pinned or task.pins:
            pins.append(
                {
                    "task_id": task.id,
                    "pinned": task.pinned,
                    "days": [[p.date.isoformat(), p.minutes] for p in task.pins],
                }
            )
            task.pins.clear()
            task.pinned = False

    record = {
        "key_result_id": kr.id,
        "from_objective_id": source.id,
        "from_position": kr.position,
        "to_objective_id": objective.id,
        "created_objective": created_objective,
        "created_quarter_id": created_quarter_id,
        "dependencies": dependencies,
        "pins": sorted(pins, key=lambda p: p["task_id"]),
    }
    in_target = KeyResult.objective_id == objective.id
    kr.position = _next_position(session, KeyResult.position, in_target)
    kr.objective = objective
    return record


def _apply_changes(session: Session, w: WhatIf, options: list[Option]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "calendar_changed": False,
        "calendar_override": None,
        "paused_objectives": [],
        "dropped_key_results": [],
        "deferred": [],
    }
    calendar_options = [o for o in options if o.kind in CALENDAR_KINDS]
    if calendar_options:
        row = _override(session, w.quarter.id)
        snapshot["calendar_changed"] = True
        snapshot["calendar_override"] = None if row is None else _row_values(row)
        new_calendar = apply_options(w.input, calendar_options).calendar
        _write_override(session, w.quarter.id, _config_values(new_calendar))
    for option in options:
        if option.kind == OptionKind.drop_objective:
            objective = session.get_one(Objective, int(option.target))
            objective.active = False
            snapshot["paused_objectives"].append(objective.id)
        elif option.kind == OptionKind.drop_kr:
            kr = session.get_one(KeyResult, int(option.target))
            kr.active = False
            snapshot["dropped_key_results"].append(kr.id)
        elif option.kind == OptionKind.defer_kr:
            kr = session.get_one(KeyResult, int(option.target))
            snapshot["deferred"].append(_defer(session, w.quarter, kr))
    return snapshot


def _reschedule(session: Session, quarter: Quarter, today: date) -> PlannedSchedule:
    session.flush()
    session.expire_all()
    planned = plan_schedule(session, quarter, today)
    persist_schedule(session, planned, plan_run_id=None)
    return planned


def apply(
    session: Session, quarter: Quarter, today: date, option_ids: list[str], key: str
) -> OptionApplication:
    """Applies the options and stores a new schedule in one transaction (committed here).

    Sending the same ``key`` again returns the stored application without applying twice.
    Raises ``OptionError`` / ``StateConflict``.
    """
    selected = [o.id for o in canonical(parse_option(option_id) for option_id in option_ids)]
    request_hash = _request_hash(quarter.id, selected)
    existing = _by_key(session, key)
    if existing is not None:
        return _replay(existing, quarter.id, request_hash)
    if not selected:
        raise OptionError("no_options", "select at least one option")

    w = load(session, quarter, today)
    options = select_options(w, option_ids)
    before = outcome(w.owners, w.base, w.input, w.planned.result)
    applied_effects = effects(session, w, options)
    snapshot = _apply_changes(session, w, options)
    planned = _reschedule(session, quarter, today)
    after = outcome(_owners(planned), w.base, planned.input, planned.result)
    row = OptionApplication(
        quarter_id=quarter.id,
        idempotency_key=key,
        request_hash=request_hash,
        option_ids=[o.id for o in options],
        snapshot=snapshot,
        before=before.model_dump(mode="json"),
        after=after.model_dump(mode="json"),
        effects=[e.model_dump(mode="json") for e in applied_effects],
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = _by_key(session, key)
        if existing is None:
            raise
        return _replay(existing, quarter.id, request_hash)
    return row


def _restore_deferred(session: Session, record: dict[str, Any]) -> None:
    kr = session.get(KeyResult, record["key_result_id"])
    if kr is None:
        return
    source = session.get(Objective, record["from_objective_id"])
    if source is None:
        raise StateConflict(
            "undo_conflict", f"objective {record['from_objective_id']} no longer exists"
        )
    moved_to = kr.objective
    kr.objective = source
    kr.position = record["from_position"]

    involved = {t for edge in record["dependencies"] for t in edge}
    alive = set(session.scalars(select(Task.id).where(Task.id.in_(involved))).all())
    present = {
        (d.task_id, d.depends_on_id)
        for d in session.scalars(
            select(TaskDependency).where(TaskDependency.task_id.in_(involved))
        ).all()
    }
    for task_id, depends_on_id in record["dependencies"]:
        if {task_id, depends_on_id} <= alive and (task_id, depends_on_id) not in present:
            session.add(TaskDependency(task_id=task_id, depends_on_id=depends_on_id))

    for pin in record["pins"]:
        task = session.get(Task, pin["task_id"])
        if task is None or task.pinned or task.pins or task.key_result_id != kr.id:
            continue
        restored = [
            TaskPin(date=date.fromisoformat(day), minutes=minutes) for day, minutes in pin["days"]
        ]
        if sum(p.minutes for p in restored) != task.estimate_minutes:
            continue
        task.pins.extend(restored)
        task.pinned = pin["pinned"]
    session.flush()

    if record["created_objective"] and moved_to.id == record["to_objective_id"]:
        remaining = session.scalar(
            select(func.count(KeyResult.id)).where(KeyResult.objective_id == moved_to.id)
        )
        if not remaining:
            session.delete(moved_to)
            session.flush()
    created_quarter = record["created_quarter_id"]
    if created_quarter is not None:
        quarter = session.get(Quarter, created_quarter)
        objectives = session.scalar(
            select(func.count(Objective.id)).where(Objective.quarter_id == created_quarter)
        )
        if quarter is not None and not objectives:
            session.delete(quarter)
            session.flush()


def undo(session: Session, application: OptionApplication, today: date) -> OptionApplication:
    """Restores the snapshot and stores a new schedule (committed here); repeating is a no-op.

    Only the latest application of a quarter that is not undone yet can be undone.
    """
    if application.undone_at is not None:
        return application
    newer = session.scalar(
        select(OptionApplication.id)
        .where(
            OptionApplication.quarter_id == application.quarter_id,
            OptionApplication.id > application.id,
            OptionApplication.undone_at.is_(None),
        )
        .limit(1)
    )
    if newer is not None:
        raise StateConflict(
            "undo_not_latest", f"undo option application {newer} first; it was applied later"
        )
    snapshot = application.snapshot
    if snapshot["calendar_changed"]:
        _write_override(session, application.quarter_id, snapshot["calendar_override"])
    for objective_id in snapshot["paused_objectives"]:
        objective = session.get(Objective, objective_id)
        if objective is not None:
            objective.active = True
    for kr_id in snapshot["dropped_key_results"]:
        kr = session.get(KeyResult, kr_id)
        if kr is not None:
            kr.active = True
    for record in reversed(snapshot["deferred"]):
        _restore_deferred(session, record)
    application.undone_at = utcnow()
    quarter = session.get_one(Quarter, application.quarter_id)
    _reschedule(session, quarter, today)
    session.commit()
    return application
