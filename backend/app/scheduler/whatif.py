"""What-if options for an overloaded quarter (ADR 0003).

Every option only rewrites the scheduler input, so its numbers come from one more ``schedule()``
run on the same data. Option ids are stable strings shared with the API:
``weekday_minutes:+60``, ``work_saturday``, ``work_sunday``, ``work_holidays``, ``drop_kr:{id}``,
``drop_objective:{id}`` and ``defer_kr:{id}``.
"""

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from itertools import combinations

from app.domain.calendar_config import DEFAULT_WORKDAY_MINUTES, MAX_WORKDAY_MINUTES
from app.scheduler.engine import schedule
from app.scheduler.models import ScheduleInput, ScheduleResult

WEEKDAY_STEP_MINUTES = 30
_WEEKDAYS = range(5)
_SATURDAY, _SUNDAY = 5, 6
_EXTRA = re.compile(r"\+?(\d{1,4})")
_ID = re.compile(r"\d{1,18}")


class OptionKind(StrEnum):
    weekday_minutes = "weekday_minutes"
    work_saturday = "work_saturday"
    work_sunday = "work_sunday"
    work_holidays = "work_holidays"
    drop_kr = "drop_kr"
    drop_objective = "drop_objective"
    defer_kr = "defer_kr"


CALENDAR_KINDS = frozenset(
    {
        OptionKind.weekday_minutes,
        OptionKind.work_saturday,
        OptionKind.work_sunday,
        OptionKind.work_holidays,
    }
)
SCOPE_KINDS = frozenset({OptionKind.drop_kr, OptionKind.drop_objective, OptionKind.defer_kr})


class OptionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_KIND_ORDER = {kind: i for i, kind in enumerate(OptionKind)}


@dataclass(frozen=True)
class Option:
    """``target`` is a KR or objective id; ``minutes`` is added to every working weekday."""

    kind: OptionKind
    target: str = ""
    minutes: int = 0

    @property
    def id(self) -> str:
        if self.kind == OptionKind.weekday_minutes:
            return f"{self.kind.value}:+{self.minutes}"
        if self.target:
            return f"{self.kind.value}:{self.target}"
        return self.kind.value


def canonical(options: Iterable[Option]) -> list[Option]:
    """Distinct options in display order: calendar changes first, then scope, by id."""
    return sorted(
        set(options), key=lambda o: (_KIND_ORDER[o.kind], len(o.target), o.target, o.minutes)
    )


def parse_option(option_id: str) -> Option:
    """Raises ``OptionError`` (``unknown_option``) for ids outside the grammar above."""
    kind_text, _, arg = option_id.partition(":")
    try:
        kind = OptionKind(kind_text)
    except ValueError:
        raise OptionError("unknown_option", f"unknown option {option_id!r}") from None
    if kind == OptionKind.weekday_minutes:
        match = _EXTRA.fullmatch(arg)
        minutes = int(match.group(1)) if match else 0
        if not 0 < minutes <= MAX_WORKDAY_MINUTES:
            raise OptionError(
                "unknown_option",
                f"{option_id!r}: extra minutes must be between 1 and {MAX_WORKDAY_MINUTES}",
            )
        return Option(kind, minutes=minutes)
    if kind in SCOPE_KINDS:
        if not _ID.fullmatch(arg):
            raise OptionError("unknown_option", f"{option_id!r} needs a numeric id")
        return Option(kind, target=str(int(arg)))
    if arg:
        raise OptionError("unknown_option", f"{option_id!r} takes no argument")
    return Option(kind)


def exclusive(a: Option, b: Option, kr_objectives: Mapping[str, str]) -> bool:
    """Options that cannot be applied together: two weekday amounts, dropping and deferring the
    same KR, or touching a KR of an objective that is dropped as a whole."""
    if a == b:
        return False
    if a.kind == b.kind == OptionKind.weekday_minutes:
        return True
    if a.kind not in SCOPE_KINDS or b.kind not in SCOPE_KINDS:
        return False
    if OptionKind.drop_objective in (a.kind, b.kind):
        if a.kind == b.kind:
            return False
        objective, kr = (a, b) if a.kind == OptionKind.drop_objective else (b, a)
        return kr_objectives.get(kr.target) == objective.target
    return a.target == b.target


def conflicting_pairs(
    options: Iterable[Option], kr_objectives: Mapping[str, str]
) -> list[tuple[Option, Option]]:
    unique = canonical(options)
    return [(a, b) for a, b in combinations(unique, 2) if exclusive(a, b, kr_objectives)]


def weekend_fill_minutes(weekdays: Sequence[int]) -> int:
    """Capacity given to a weekend day that is switched on without a configured capacity."""
    return max(weekdays[:5]) or DEFAULT_WORKDAY_MINUTES


def apply_options(inp: ScheduleInput, options: Iterable[Option]) -> ScheduleInput:
    """The input as if ``options`` were applied; they must be free of conflicts.

    Tasks of a dropped or deferred KR (or dropped objective) leave the input, and dependencies
    on them count as satisfied, exactly like tasks of an inactive objective.
    """
    calendar = inp.calendar
    base = calendar.weekday_capacity_minutes
    weekdays = list(base)
    switches = {
        "work_saturday": calendar.work_saturday,
        "work_sunday": calendar.work_sunday,
        "work_holidays": calendar.work_holidays,
    }
    makeup = calendar.makeup_day_capacity_minutes
    dropped_krs: set[str] = set()
    dropped_objectives: set[str] = set()
    for option in options:
        if option.kind == OptionKind.weekday_minutes:
            for day in _WEEKDAYS:
                if base[day] > 0:
                    weekdays[day] = min(base[day] + option.minutes, MAX_WORKDAY_MINUTES)
            makeup = max(weekdays[:5]) or makeup
        elif option.kind == OptionKind.work_saturday:
            switches["work_saturday"] = True
            weekdays[_SATURDAY] = base[_SATURDAY] or weekend_fill_minutes(base)
        elif option.kind == OptionKind.work_sunday:
            switches["work_sunday"] = True
            weekdays[_SUNDAY] = base[_SUNDAY] or weekend_fill_minutes(base)
        elif option.kind == OptionKind.work_holidays:
            switches["work_holidays"] = True
        elif option.kind == OptionKind.drop_objective:
            dropped_objectives.add(option.target)
        else:
            dropped_krs.add(option.target)

    new_calendar = calendar.model_copy(
        update={
            "weekday_capacity_minutes": tuple(weekdays),
            "makeup_day_capacity_minutes": makeup,
            **switches,
        }
    )
    kept = []
    removed = set(inp.done_task_ids)
    for task in inp.tasks:
        if task.kr_id in dropped_krs or task.objective_id in dropped_objectives:
            removed.add(task.id)
        else:
            kept.append(task)
    return inp.model_copy(
        update={"calendar": new_calendar, "tasks": tuple(kept), "done_task_ids": frozenset(removed)}
    )


def run_options(inp: ScheduleInput, options: Iterable[Option]) -> ScheduleResult:
    return schedule(apply_options(inp, options))


def not_red(result: ScheduleResult) -> bool:
    return result.feasibility.status != "red"


def green(result: ScheduleResult) -> bool:
    return result.feasibility.status == "green"


@dataclass(frozen=True)
class WeekdaySearch:
    minutes: int
    result: ScheduleResult


def min_weekday_extra(
    inp: ScheduleInput,
    accept: Callable[[ScheduleResult], bool],
    others: Sequence[Option] = (),
    step: int = WEEKDAY_STEP_MINUTES,
) -> WeekdaySearch | None:
    """Smallest multiple of ``step`` minutes added to every working weekday that makes
    ``accept`` true (together with ``others``), found by binary search.

    ``None`` when even the maximum working day is not enough. The returned result is always
    one that was actually computed and accepted, so the answer holds even where list
    scheduling is not perfectly monotonic.
    """
    working = [inp.calendar.weekday_capacity_minutes[d] for d in _WEEKDAYS]
    working = [m for m in working if m > 0]
    if not working or min(working) >= MAX_WORKDAY_MINUTES:
        return None
    top = -(-(MAX_WORKDAY_MINUTES - min(working)) // step)
    cache: dict[int, ScheduleResult] = {}

    def result_at(steps: int) -> ScheduleResult:
        if steps not in cache:
            extra = [Option(OptionKind.weekday_minutes, minutes=steps * step)] if steps else []
            cache[steps] = run_options(inp, [*others, *extra])
        return cache[steps]

    if accept(result_at(0)):
        return WeekdaySearch(0, cache[0])
    if not accept(result_at(top)):
        return None
    low, high = 0, top
    while high - low > 1:
        middle = (low + high) // 2
        if accept(result_at(middle)):
            high = middle
        else:
            low = middle
    return WeekdaySearch(high * step, cache[high])


@dataclass(frozen=True)
class Measures:
    """Numbers shown for one scheduler run; minutes throughout."""

    demand_minutes: int
    supply_minutes: int
    shortfall_minutes: int
    late_task_count: int
    buffer_minutes: int
    buffer_used_minutes: int
    finish_date: date | None


def measure(inp: ScheduleInput, result: ScheduleResult) -> Measures:
    """``shortfall`` is the estimate of the tasks that do not fit; ``buffer_used`` the minutes
    scheduled on buffer days."""
    estimates = {task.id: task.estimate_minutes for task in inp.tasks}
    feasibility = result.feasibility
    buffer_start = feasibility.buffer_start
    buffer_used = 0
    if buffer_start is not None:
        buffer_used = sum(
            a.minutes
            for placed in result.scheduled
            for a in placed.allocations
            if a.date >= buffer_start
        )
    return Measures(
        demand_minutes=feasibility.demand_minutes,
        supply_minutes=feasibility.supply_minutes,
        shortfall_minutes=sum(estimates[t] for t in feasibility.late_task_ids),
        late_task_count=len(feasibility.late_task_ids),
        buffer_minutes=feasibility.supply_minutes - feasibility.buffered_supply_minutes,
        buffer_used_minutes=buffer_used,
        finish_date=max((s.end_date for s in result.scheduled), default=None),
    )
