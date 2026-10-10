from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.calendar_config import CalendarConfig


def test_defaults_are_four_hours_on_weekdays_and_nothing_on_weekends() -> None:
    config = CalendarConfig()
    assert config.weekday_capacity_minutes == (240, 240, 240, 240, 240, 0, 0)
    assert not (config.work_saturday or config.work_sunday or config.work_holidays)
    assert config.leave_days == frozenset()
    assert config.makeup_days == frozenset()


@pytest.mark.parametrize(
    "capacities",
    [
        (240, 240, 240, 240, 240, 0),
        (240, 240, 240, 240, 240, 0, 0, 0),
        (-1, 240, 240, 240, 240, 0, 0),
        (1441, 240, 240, 240, 240, 0, 0),
    ],
)
def test_rejects_invalid_weekday_capacities(capacities: tuple[int, ...]) -> None:
    with pytest.raises(ValidationError):
        CalendarConfig.model_validate({"weekday_capacity_minutes": capacities})


def test_rejects_non_positive_makeup_capacity() -> None:
    with pytest.raises(ValidationError):
        CalendarConfig(makeup_day_capacity_minutes=0)


def test_rejects_date_that_is_both_leave_and_makeup() -> None:
    day = date(2026, 10, 10)
    with pytest.raises(ValidationError, match="2026-10-10"):
        CalendarConfig(leave_days=frozenset({day}), makeup_days=frozenset({day}))


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CalendarConfig.model_validate({"work_friday": True})


def test_round_trips_through_json() -> None:
    config = CalendarConfig(
        work_saturday=True,
        leave_days=frozenset({date(2026, 10, 5)}),
        makeup_days=frozenset({date(2026, 10, 10)}),
    )
    assert CalendarConfig.model_validate_json(config.model_dump_json()) == config
