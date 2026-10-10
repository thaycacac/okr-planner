from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.calendar import load_holidays
from app.domain.calendar_config import CalendarConfig
from app.scheduler import (
    Allocation,
    ScheduleInputError,
    ScheduleResult,
    buffer_start_index,
    schedule,
)
from tests.scheduler_factories import Q4_2026, make_input, make_task

# Q4 2026 starts on Thursday 2026-10-01; 2026-10-03/04 is the first weekend.
THU = date(2026, 10, 1)
FRI = date(2026, 10, 2)
SAT = date(2026, 10, 3)
MON = date(2026, 10, 5)
TUE = date(2026, 10, 6)
WED = date(2026, 10, 7)
NEXT_SAT = date(2026, 10, 10)


def placed(result: ScheduleResult, task_id: str) -> tuple[Allocation, ...]:
    return {s.task_id: s for s in result.scheduled}[task_id].allocations


def pairs(allocs: tuple[Allocation, ...]) -> list[tuple[date, int]]:
    return [(a.date, a.minutes) for a in allocs]


def dates_between(start: date, end: date) -> frozenset[date]:
    return frozenset(start + timedelta(days=i) for i in range((end - start).days + 1))


class TestListScheduling:
    def test_task_spreads_over_following_working_days(self) -> None:
        result = schedule(make_input(make_task("a", 600)))
        assert pairs(placed(result, "a")) == [(THU, 240), (FRI, 240), (MON, 120)]

    def test_multi_day_task_shares_its_last_day_with_the_next_task(self) -> None:
        result = schedule(make_input(make_task("a", 300, order=1), make_task("b", 300, order=2)))
        assert pairs(placed(result, "a")) == [(THU, 240), (FRI, 60)]
        assert pairs(placed(result, "b")) == [(FRI, 180), (MON, 120)]

    def test_dependent_starts_the_day_after_its_dependency_ends(self) -> None:
        result = schedule(make_input(make_task("a", 60), make_task("b", 60, deps=["a"])))
        assert pairs(placed(result, "a")) == [(THU, 60)]
        assert pairs(placed(result, "b")) == [(FRI, 60)]

    def test_free_capacity_before_a_dependent_is_used_by_other_tasks(self) -> None:
        result = schedule(
            make_input(
                make_task("a", 60, order=1),
                make_task("b", 60, order=2, deps=["a"]),
                make_task("c", 60, order=3),
            )
        )
        assert pairs(placed(result, "c")) == [(THU, 60)]
        assert pairs(placed(result, "b")) == [(FRI, 60)]

    def test_dependency_on_a_finished_task_is_satisfied(self) -> None:
        result = schedule(make_input(make_task("b", 60, deps=["done-1"]), done=["done-1"]))
        assert pairs(placed(result, "b")) == [(THU, 60)]

    def test_weekends_holidays_and_leave_are_skipped(self) -> None:
        calendar = CalendarConfig(leave_days=frozenset({MON}))
        result = schedule(make_input(make_task("a", 720), calendar=calendar, holidays=[FRI]))
        assert pairs(placed(result, "a")) == [(THU, 240), (TUE, 240), (WED, 240)]

    def test_enabled_saturday_is_used(self) -> None:
        calendar = CalendarConfig(
            weekday_capacity_minutes=(240, 240, 240, 240, 240, 120, 0), work_saturday=True
        )
        result = schedule(make_input(make_task("a", 540), calendar=calendar))
        assert pairs(placed(result, "a")) == [(THU, 240), (FRI, 240), (SAT, 60)]


class TestWindow:
    def test_window_starts_today_so_overdue_work_moves_forward(self) -> None:
        result = schedule(make_input(make_task("a", 60), today=date(2026, 11, 10)))
        assert result.window_start == date(2026, 11, 10)
        assert pairs(placed(result, "a")) == [(date(2026, 11, 10), 60)]

    def test_window_starts_at_quarter_start_when_today_is_earlier(self) -> None:
        result = schedule(make_input(make_task("a", 60), today=date(2026, 9, 1)))
        assert result.window_start == THU
        assert result.window_end == date(2026, 12, 31)

    def test_nothing_fits_after_the_quarter_has_ended(self) -> None:
        result = schedule(make_input(make_task("a", 60), today=date(2027, 1, 5)))
        assert result.scheduled == ()
        assert [(u.task_id, u.reason) for u in result.unscheduled] == [("a", "exceeds_quarter")]
        assert result.feasibility.supply_minutes == 0
        assert result.feasibility.buffer_start is None


class TestPriority:
    def test_objective_priority_is_strict_regardless_of_input_order(self) -> None:
        # Only Thursday and Friday of the quarter are available.
        calendar = CalendarConfig(leave_days=dates_between(MON, Q4_2026.end))
        low = make_task("low", 240, priority=2, order=0)
        high = make_task("high", 480, priority=1, order=9)
        result = schedule(make_input(low, high, calendar=calendar))
        assert pairs(placed(result, "high")) == [(THU, 240), (FRI, 240)]
        assert [u.task_id for u in result.unscheduled] == ["low"]

    def test_tie_break_is_kr_order_then_task_order_then_id(self) -> None:
        result = schedule(
            make_input(
                make_task("z", 240, kr_order=1, order=2),
                make_task("b", 240, kr_order=1, order=1),
                make_task("a", 240, kr_order=1, order=1),
                make_task("y", 240, kr_order=0, order=5),
            )
        )
        starts = {s.task_id: s.start_date for s in result.scheduled}
        assert starts == {"y": THU, "a": FRI, "b": MON, "z": TUE}


class TestBuffer:
    @pytest.mark.parametrize(
        ("capacities", "expected"),
        [
            ([], None),
            ([0, 0], None),
            ([60] * 10, 9),
            ([60] * 11, 9),
            ([10, 10, 10, 70], 3),
            ([100], 0),
        ],
    )
    def test_buffer_start_is_shortest_suffix_holding_ten_percent(
        self, capacities: list[int], expected: int | None
    ) -> None:
        assert buffer_start_index(capacities) == expected

    def test_task_within_buffer_is_scheduled_with_yellow_warning(self) -> None:
        # From Fri 2026-12-18 there are 10 working days of 240 minutes: the buffer is the last day.
        result = schedule(make_input(make_task("a", 240 * 9 + 1), today=date(2026, 12, 18)))
        assert result.feasibility.buffer_start == date(2026, 12, 31)
        assert placed(result, "a")[-1] == Allocation(date=date(2026, 12, 31), minutes=1)
        assert result.scheduled[0].uses_buffer
        assert [(w.code, w.level, w.task_ids) for w in result.warnings] == [
            ("uses_buffer", "yellow", ("a",))
        ]
        assert result.feasibility.status == "yellow"

    def test_task_before_buffer_is_green(self) -> None:
        result = schedule(make_input(make_task("a", 240 * 9), today=date(2026, 12, 18)))
        assert result.warnings == ()
        assert result.feasibility.status == "green"

    @pytest.mark.parametrize(
        ("calendar", "supply_hours", "buffer_hours"),
        [
            (CalendarConfig(), 260, 28),
            (
                CalendarConfig(
                    weekday_capacity_minutes=(240, 240, 240, 240, 240, 240, 0), work_saturday=True
                ),
                312,
                32,
            ),
        ],
    )
    def test_buffer_is_rounded_up_to_whole_days(
        self, calendar: CalendarConfig, supply_hours: int, buffer_hours: int
    ) -> None:
        holidays = load_holidays([2026]).holiday_dates
        feasibility = schedule(make_input(calendar=calendar, holidays=holidays)).feasibility
        assert feasibility.supply_minutes == supply_hours * 60
        assert feasibility.buffer_start == date(2026, 12, 23)
        assert feasibility.supply_minutes - feasibility.buffered_supply_minutes == buffer_hours * 60

    def test_buffered_supply_excludes_every_buffer_day(self) -> None:
        # 11 days of 240 minutes: 10% is 264 minutes, so the buffer takes the last two days.
        result = schedule(make_input(today=date(2026, 12, 17)))
        assert result.feasibility.supply_minutes == 2640
        assert result.feasibility.buffer_start == date(2026, 12, 30)
        assert result.feasibility.buffered_supply_minutes == 2160


class TestOverload:
    def test_task_past_quarter_end_is_red_and_leaves_capacity_for_others(self) -> None:
        result = schedule(
            make_input(
                make_task("big", 240 * 11, order=1, kr_id="kr-big", objective_id="o-big"),
                make_task("after-big", 60, order=2, deps=["big"], kr_id="kr-dep"),
                make_task("small", 240 * 10, order=3),
                today=date(2026, 12, 18),
            )
        )
        assert [(u.task_id, u.reason) for u in result.unscheduled] == [
            ("after-big", "dependency_unscheduled"),
            ("big", "exceeds_quarter"),
        ]
        assert sum(a.minutes for a in placed(result, "small")) == 2400
        red = {w.code: w.task_ids for w in result.warnings if w.level == "red"}
        assert red == {"exceeds_quarter": ("big",), "dependency_unscheduled": ("after-big",)}
        assert result.feasibility.status == "red"
        assert result.feasibility.late_task_ids == ("after-big", "big")
        assert result.feasibility.late_kr_ids == ("kr-big", "kr-dep")
        assert result.feasibility.late_objective_ids == ("o-big", "o1")

    def test_feasibility_reports_demand_supply_and_buffered_supply(self) -> None:
        result = schedule(
            make_input(make_task("a", 100), make_task("b", 200), today=date(2026, 12, 18))
        )
        assert result.feasibility.demand_minutes == 300
        assert result.feasibility.supply_minutes == 2400
        assert result.feasibility.buffered_supply_minutes == 2160


class TestPinned:
    def test_pin_is_kept_and_consumes_capacity_first(self) -> None:
        result = schedule(
            make_input(
                make_task("free", 240, priority=1),
                make_task("pin", 180, priority=3, pins=[(THU, 180)]),
            )
        )
        assert pairs(placed(result, "pin")) == [(THU, 180)]
        assert pairs(placed(result, "free")) == [(THU, 60), (FRI, 180)]
        assert result.warnings == ()

    def test_dependent_of_pin_starts_after_the_pin(self) -> None:
        result = schedule(
            make_input(make_task("pin", 60, pins=[(MON, 60)]), make_task("b", 60, deps=["pin"]))
        )
        assert pairs(placed(result, "b")) == [(TUE, 60)]

    def test_pins_over_capacity_warn_and_block_other_tasks_on_that_day(self) -> None:
        result = schedule(
            make_input(
                make_task("p1", 200, pins=[(THU, 200)]),
                make_task("p2", 100, pins=[(THU, 100)]),
                make_task("free", 60),
            )
        )
        assert pairs(placed(result, "p1")) == [(THU, 200)]
        assert pairs(placed(result, "p2")) == [(THU, 100)]
        assert pairs(placed(result, "free")) == [(FRI, 60)]
        assert [(w.code, w.task_ids, w.dates) for w in result.warnings] == [
            ("pinned_over_capacity", ("p1", "p2"), (THU,))
        ]

    @pytest.mark.parametrize(
        ("pin_date", "code"),
        [
            (NEXT_SAT, "pinned_non_working_day"),
            (date(2026, 10, 2), "pinned_overdue"),
            (date(2027, 1, 4), "pinned_outside_quarter"),
            (date(2026, 9, 30), "pinned_outside_quarter"),
        ],
    )
    def test_pin_on_unavailable_day_is_kept_with_red_warning(
        self, pin_date: date, code: str
    ) -> None:
        result = schedule(make_input(make_task("pin", 60, pins=[(pin_date, 60)]), today=MON))
        assert pairs(placed(result, "pin")) == [(pin_date, 60)]
        assert [(w.code, w.level, w.dates) for w in result.warnings] == [(code, "red", (pin_date,))]

    def test_pin_before_its_dependency_warns_without_moving(self) -> None:
        result = schedule(
            make_input(make_task("a", 480), make_task("pin", 60, deps=["a"], pins=[(FRI, 60)]))
        )
        assert pairs(placed(result, "pin")) == [(FRI, 60)]
        assert pairs(placed(result, "a")) == [(THU, 240), (FRI, 180), (MON, 60)]
        assert [(w.code, w.task_ids) for w in result.warnings] == [
            ("pinned_dependency_conflict", ("a", "pin"))
        ]

    def test_pins_must_cover_the_estimate(self) -> None:
        with pytest.raises(ValidationError, match="pins 60 minutes but estimates 120"):
            make_task("pin", 120, pins=[(THU, 60)])

    def test_pins_cannot_repeat_a_date(self) -> None:
        with pytest.raises(ValidationError, match="same date"):
            make_task("pin", 120, pins=[(THU, 60), (THU, 60)])


class TestInputErrors:
    def test_cycle_is_rejected_with_the_loop(self) -> None:
        with pytest.raises(ScheduleInputError) as info:
            schedule(
                make_input(
                    make_task("a", 60, deps=["c"]),
                    make_task("b", 60, deps=["a"]),
                    make_task("c", 60, deps=["b"]),
                    make_task("d", 60),
                )
            )
        assert info.value.code == "dependency_cycle"
        assert info.value.task_ids == ("a", "b", "c")
        assert "a -> b -> c -> a" in str(info.value)

    def test_self_dependency_is_a_cycle(self) -> None:
        with pytest.raises(ScheduleInputError) as info:
            schedule(make_input(make_task("a", 60, deps=["a"])))
        assert (info.value.code, info.value.task_ids) == ("dependency_cycle", ("a",))

    def test_unknown_dependency_is_rejected(self) -> None:
        with pytest.raises(ScheduleInputError) as info:
            schedule(make_input(make_task("a", 60, deps=["ghost"])))
        assert (info.value.code, info.value.task_ids) == ("unknown_dependency", ("ghost",))

    def test_duplicate_task_id_is_rejected(self) -> None:
        with pytest.raises(ScheduleInputError) as info:
            schedule(make_input(make_task("a", 60), make_task("a", 30)))
        assert (info.value.code, info.value.task_ids) == ("duplicate_task_id", ("a",))
