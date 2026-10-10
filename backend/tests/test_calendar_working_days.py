from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.calendar import load_holidays, working_days
from app.domain.calendar_config import CalendarConfig

# Week of Mon 2026-10-05 .. Sun 2026-10-11, no VN holidays inside.
MON = date(2026, 10, 5)
WED = date(2026, 10, 7)
SAT = date(2026, 10, 10)
SUN = date(2026, 10, 11)
NO_HOLIDAYS: frozenset[date] = frozenset()
WEEKEND_CAPACITY = (240, 240, 240, 240, 240, 120, 90)


def dates_of(config: CalendarConfig, holidays: frozenset[date] = NO_HOLIDAYS) -> list[date]:
    return [d for d, _ in working_days(MON, SUN, config, holidays)]


def test_default_week_is_monday_to_friday_at_240_minutes() -> None:
    result = working_days(MON, SUN, CalendarConfig(), NO_HOLIDAYS)
    assert result == [(MON + timedelta(days=i), 240) for i in range(5)]


def test_range_is_inclusive_on_both_ends() -> None:
    assert working_days(WED, WED, CalendarConfig(), NO_HOLIDAYS) == [(WED, 240)]


def test_empty_when_start_after_end() -> None:
    assert working_days(SUN, MON, CalendarConfig(), NO_HOLIDAYS) == []


def test_weekday_with_zero_capacity_is_not_a_working_day() -> None:
    config = CalendarConfig(weekday_capacity_minutes=(240, 240, 0, 240, 240, 0, 0))
    assert WED not in dates_of(config)


def test_capacity_follows_weekday() -> None:
    config = CalendarConfig(weekday_capacity_minutes=(60, 120, 180, 240, 300, 0, 0))
    result = working_days(MON, SUN, config, NO_HOLIDAYS)
    assert [c for _, c in result] == [60, 120, 180, 240, 300]


def test_saturday_only_when_enabled() -> None:
    capacities = CalendarConfig(weekday_capacity_minutes=WEEKEND_CAPACITY)
    assert SAT not in dates_of(capacities)
    enabled = capacities.model_copy(update={"work_saturday": True})
    assert (SAT, 120) in working_days(MON, SUN, enabled, NO_HOLIDAYS)
    assert SUN not in dates_of(enabled)


def test_sunday_only_when_enabled() -> None:
    capacities = CalendarConfig(weekday_capacity_minutes=WEEKEND_CAPACITY)
    assert SUN not in dates_of(capacities)
    enabled = capacities.model_copy(update={"work_sunday": True})
    assert (SUN, 90) in working_days(MON, SUN, enabled, NO_HOLIDAYS)
    assert SAT not in dates_of(enabled)


def test_enabled_weekend_with_zero_capacity_is_still_excluded() -> None:
    config = CalendarConfig(work_saturday=True, work_sunday=True)
    assert SAT not in dates_of(config)
    assert SUN not in dates_of(config)


def test_holiday_only_when_working_on_holidays_is_enabled() -> None:
    holidays = frozenset({WED})
    assert WED not in dates_of(CalendarConfig(), holidays)
    assert WED in dates_of(CalendarConfig(work_holidays=True), holidays)


def test_holiday_on_enabled_saturday_still_requires_holiday_switch() -> None:
    config = CalendarConfig(weekday_capacity_minutes=WEEKEND_CAPACITY, work_saturday=True)
    holidays = frozenset({SAT})
    assert SAT not in dates_of(config, holidays)
    assert SAT in dates_of(config.model_copy(update={"work_holidays": True}), holidays)


def test_leave_day_is_excluded_even_when_everything_is_enabled() -> None:
    config = CalendarConfig(
        weekday_capacity_minutes=WEEKEND_CAPACITY,
        work_saturday=True,
        work_holidays=True,
        leave_days=frozenset({WED, SAT}),
    )
    result = dates_of(config, frozenset({WED}))
    assert WED not in result
    assert SAT not in result


def test_makeup_day_is_always_a_working_day() -> None:
    config = CalendarConfig(makeup_days=frozenset({SAT, SUN, WED}), makeup_day_capacity_minutes=180)
    result = working_days(MON, SUN, config, frozenset({WED}))
    assert (SAT, 180) in result
    assert (SUN, 180) in result
    assert (WED, 180) in result


def test_makeup_day_overrides_zero_weekday_capacity() -> None:
    config = CalendarConfig(
        weekday_capacity_minutes=(240, 240, 0, 240, 240, 0, 0), makeup_days=frozenset({WED})
    )
    assert (WED, 240) in working_days(MON, SUN, config, NO_HOLIDAYS)


def test_accepts_any_collection_of_holidays() -> None:
    assert WED not in [d for d, _ in working_days(MON, SUN, CalendarConfig(), [WED])]


def test_vn_tet_2026_week_has_no_working_days_by_default() -> None:
    holidays = load_holidays([2026]).holiday_dates
    assert working_days(date(2026, 2, 14), date(2026, 2, 22), CalendarConfig(), holidays) == []


def test_vn_national_day_2026_with_official_makeup_saturday() -> None:
    vn = load_holidays([2026])
    config = CalendarConfig(makeup_days=vn.makeup_dates)
    result = [
        d for d, _ in working_days(date(2026, 8, 22), date(2026, 9, 4), config, vn.holiday_dates)
    ]
    assert date(2026, 8, 22) in result
    assert not {date(2026, 8, 31), date(2026, 9, 1), date(2026, 9, 2)} & set(result)
    assert date(2026, 9, 3) in result


# --- property tests -------------------------------------------------------------------------

DAY_MIN = date(2026, 1, 1)
DAY_MAX = date(2027, 12, 31)

days = st.dates(min_value=DAY_MIN, max_value=DAY_MAX)
capacity = st.integers(min_value=0, max_value=600)
positive_capacity = st.integers(min_value=1, max_value=600)


@st.composite
def date_ranges(draw: st.DrawFn) -> tuple[date, date]:
    start = draw(days)
    length = draw(st.integers(min_value=0, max_value=120))
    return start, min(start + timedelta(days=length), DAY_MAX)


@st.composite
def configs(draw: st.DrawFn, weekday_capacity: st.SearchStrategy[int] = capacity) -> CalendarConfig:
    leave = draw(st.frozensets(days, max_size=15))
    makeup = draw(st.frozensets(days, max_size=5)) - leave
    return CalendarConfig(
        weekday_capacity_minutes=tuple(draw(weekday_capacity) for _ in range(7)),
        work_saturday=draw(st.booleans()),
        work_sunday=draw(st.booleans()),
        work_holidays=draw(st.booleans()),
        leave_days=leave,
        makeup_days=makeup,
        makeup_day_capacity_minutes=draw(positive_capacity),
    )


holiday_sets = st.one_of(
    st.frozensets(days, max_size=30),
    st.just(load_holidays().holiday_dates),
)


def all_days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


@given(rng=date_ranges(), config=configs(), holidays=holiday_sets)
def test_result_is_sorted_within_range_with_positive_capacity(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date]
) -> None:
    start, end = rng
    result = working_days(start, end, config, holidays)
    result_dates = [d for d, _ in result]
    assert result_dates == sorted(set(result_dates))
    assert all(start <= d <= end and c > 0 for d, c in result)


@given(rng=date_ranges(), config=configs(), holidays=holiday_sets, weekday=st.sampled_from([5, 6]))
def test_disabled_weekend_day_never_appears(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date], weekday: int
) -> None:
    switch = "work_saturday" if weekday == 5 else "work_sunday"
    config = config.model_copy(update={switch: False})
    result = working_days(*rng, config, holidays)
    assert not [d for d, _ in result if d.weekday() == weekday and d not in config.makeup_days]


@given(rng=date_ranges(), config=configs(), holidays=holiday_sets)
def test_disabled_holidays_never_appear(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date]
) -> None:
    config = config.model_copy(update={"work_holidays": False})
    result = working_days(*rng, config, holidays)
    assert not [d for d, _ in result if d in holidays and d not in config.makeup_days]


@given(
    rng=date_ranges(),
    config=configs(weekday_capacity=positive_capacity),
    holidays=holiday_sets,
    weekday=st.sampled_from([5, 6]),
)
def test_enabled_weekend_day_appears(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date], weekday: int
) -> None:
    switch = "work_saturday" if weekday == 5 else "work_sunday"
    config = config.model_copy(update={switch: True, "work_holidays": True})
    result = dict(working_days(*rng, config, holidays))
    expected = [d for d in all_days(*rng) if d.weekday() == weekday and d not in config.leave_days]
    for d in expected:
        assert d in result
        if d not in config.makeup_days:
            assert result[d] == config.weekday_capacity_minutes[weekday]


@given(rng=date_ranges(), config=configs(weekday_capacity=positive_capacity), holidays=holiday_sets)
def test_enabled_holidays_appear(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date]
) -> None:
    config = config.model_copy(
        update={"work_holidays": True, "work_saturday": True, "work_sunday": True}
    )
    result = dict(working_days(*rng, config, holidays))
    for d in all_days(*rng):
        if d in holidays and d not in config.leave_days:
            assert d in result


@given(rng=date_ranges(), config=configs(), holidays=holiday_sets)
def test_leave_never_appears_and_makeup_always_appears(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date]
) -> None:
    start, end = rng
    result = dict(working_days(start, end, config, holidays))
    assert not config.leave_days & result.keys()
    for d in config.makeup_days:
        if start <= d <= end:
            assert result[d] == config.makeup_day_capacity_minutes


@given(rng=date_ranges(), config=configs(), holidays=holiday_sets)
def test_is_deterministic_and_order_independent(
    rng: tuple[date, date], config: CalendarConfig, holidays: frozenset[date]
) -> None:
    first = working_days(*rng, config, holidays)
    assert working_days(*rng, config, sorted(holidays, reverse=True)) == first
