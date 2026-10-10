from collections.abc import Collection
from datetime import date, timedelta
from typing import NamedTuple

from app.domain.calendar_config import CalendarConfig

SATURDAY = 5
SUNDAY = 6


class WorkingDay(NamedTuple):
    date: date
    capacity_minutes: int


def day_capacity_minutes(day: date, config: CalendarConfig, holidays: Collection[date]) -> int:
    """Capacity of ``day``; 0 means it is not a working day.

    Precedence: make-up day > leave > weekend switch > holiday switch > weekday capacity.
    """
    if day in config.makeup_days:
        return config.makeup_day_capacity_minutes
    if day in config.leave_days:
        return 0
    weekday = day.weekday()
    if (weekday == SATURDAY and not config.work_saturday) or (
        weekday == SUNDAY and not config.work_sunday
    ):
        return 0
    if day in holidays and not config.work_holidays:
        return 0
    return config.weekday_capacity_minutes[weekday]


def working_days(
    start: date, end: date, config: CalendarConfig, holidays: Collection[date]
) -> list[WorkingDay]:
    """Working days in the inclusive range ``[start, end]`` in ascending order.

    Only days with positive capacity are returned; an empty list when ``start > end``.
    """
    holiday_set = frozenset(holidays)
    result: list[WorkingDay] = []
    day = start
    while day <= end:
        capacity = day_capacity_minutes(day, config, holiday_set)
        if capacity > 0:
            result.append(WorkingDay(day, capacity))
        day += timedelta(days=1)
    return result
