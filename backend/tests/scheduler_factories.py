from collections.abc import Iterable
from datetime import date

from app.domain.calendar_config import CalendarConfig
from app.domain.quarter import Quarter
from app.scheduler import Allocation, ScheduleInput, SchedulerTask

Q4_2026 = Quarter(year=2026, number=4)


def make_task(
    task_id: str,
    minutes: int,
    *,
    priority: int = 1,
    kr_order: int = 1,
    order: int = 0,
    deps: Iterable[str] = (),
    pins: Iterable[tuple[date, int]] = (),
    objective_id: str | None = None,
    kr_id: str | None = None,
) -> SchedulerTask:
    return SchedulerTask(
        id=task_id,
        objective_id=objective_id or f"o{priority}",
        kr_id=kr_id or f"o{priority}-kr{kr_order}",
        estimate_minutes=minutes,
        objective_priority=priority,
        kr_order=kr_order,
        task_order=order,
        depends_on=frozenset(deps),
        pinned_allocations=tuple(Allocation(date=d, minutes=m) for d, m in pins),
    )


def make_input(
    *tasks: SchedulerTask,
    today: date = date(2026, 10, 1),
    quarter: Quarter = Q4_2026,
    calendar: CalendarConfig | None = None,
    holidays: Iterable[date] = (),
    done: Iterable[str] = (),
) -> ScheduleInput:
    return ScheduleInput(
        quarter=quarter,
        today=today,
        calendar=calendar or CalendarConfig(),
        holidays=frozenset(holidays),
        tasks=tasks,
        done_task_ids=frozenset(done),
    )
