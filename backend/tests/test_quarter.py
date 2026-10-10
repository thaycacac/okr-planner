from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.domain.quarter import Quarter


def test_q4_bounds() -> None:
    q = Quarter(year=2026, number=4)
    assert (q.start, q.end) == (date(2026, 10, 1), date(2026, 12, 31))


def test_q1_leap_year_end() -> None:
    assert Quarter(year=2028, number=1).end == date(2028, 3, 31)


@given(
    year=st.integers(min_value=2000, max_value=2099),
    number=st.integers(min_value=1, max_value=3),
)
def test_quarters_are_contiguous(year: int, number: int) -> None:
    current = Quarter(year=year, number=number)
    following = Quarter(year=year, number=number + 1)
    assert current.end + timedelta(days=1) == following.start
