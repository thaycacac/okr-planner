from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

MINUTES_PER_DAY = 24 * 60
DEFAULT_WORKDAY_MINUTES = 4 * 60
MAX_WORKDAY_MINUTES = 12 * 60

CapacityMinutes = Annotated[int, Field(ge=0, le=MINUTES_PER_DAY)]
WeekdayCapacities = tuple[
    CapacityMinutes,
    CapacityMinutes,
    CapacityMinutes,
    CapacityMinutes,
    CapacityMinutes,
    CapacityMinutes,
    CapacityMinutes,
]


class CalendarConfig(BaseModel):
    """User working-time settings; capacity is in whole minutes to keep comparisons exact.

    ``weekday_capacity_minutes`` is indexed by ``date.weekday()`` (Monday = 0 ... Sunday = 6).
    Make-up days are always working days and use ``makeup_day_capacity_minutes``, overriding
    the weekend/holiday switches; a date cannot be both a leave day and a make-up day.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    weekday_capacity_minutes: WeekdayCapacities = (
        DEFAULT_WORKDAY_MINUTES,
        DEFAULT_WORKDAY_MINUTES,
        DEFAULT_WORKDAY_MINUTES,
        DEFAULT_WORKDAY_MINUTES,
        DEFAULT_WORKDAY_MINUTES,
        0,
        0,
    )
    work_saturday: bool = False
    work_sunday: bool = False
    work_holidays: bool = False
    leave_days: frozenset[date] = frozenset()
    makeup_days: frozenset[date] = frozenset()
    makeup_day_capacity_minutes: int = Field(
        default=DEFAULT_WORKDAY_MINUTES, gt=0, le=MINUTES_PER_DAY
    )

    @model_validator(mode="after")
    def _leave_and_makeup_are_disjoint(self) -> Self:
        overlap = self.leave_days & self.makeup_days
        if overlap:
            dates = ", ".join(d.isoformat() for d in sorted(overlap))
            raise ValueError(f"dates cannot be both leave and make-up days: {dates}")
        return self
