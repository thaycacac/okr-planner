"""What-if options only rewrite the scheduler input; each result is a real scheduler run."""

from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.domain.calendar_config import MAX_WORKDAY_MINUTES, CalendarConfig
from app.scheduler import ScheduleInput, schedule
from app.scheduler.whatif import (
    WEEKDAY_STEP_MINUTES,
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
    run_options,
)
from tests.scheduler_factories import make_input, make_task
from tests.test_scheduler_properties import assert_invariants, schedule_inputs, vn_holidays

HOLIDAY = date(2026, 11, 24)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("weekday_minutes:+60", Option(OptionKind.weekday_minutes, minutes=60)),
        ("weekday_minutes:90", Option(OptionKind.weekday_minutes, minutes=90)),
        ("work_saturday", Option(OptionKind.work_saturday)),
        ("work_holidays", Option(OptionKind.work_holidays)),
        ("drop_kr:007", Option(OptionKind.drop_kr, target="7")),
        ("drop_objective:3", Option(OptionKind.drop_objective, target="3")),
        ("defer_kr:12", Option(OptionKind.defer_kr, target="12")),
    ],
)
def test_option_ids_parse_to_a_canonical_form(text: str, expected: Option) -> None:
    option = parse_option(text)
    assert option == expected
    assert parse_option(option.id) == option


def test_canonical_order_puts_calendar_changes_first() -> None:
    ids = ["defer_kr:12", "work_saturday", "drop_kr:3", "defer_kr:3", "work_saturday"]
    assert [o.id for o in canonical(parse_option(i) for i in ids)] == [
        "work_saturday",
        "drop_kr:3",
        "defer_kr:3",
        "defer_kr:12",
    ]


@pytest.mark.parametrize(
    "text",
    [
        "ai_trim",
        "weekday_minutes:+0",
        "weekday_minutes:-60",
        f"weekday_minutes:+{MAX_WORKDAY_MINUTES + 1}",
        "work_saturday:1",
        "drop_kr",
        "defer_kr:abc",
    ],
)
def test_malformed_option_ids_are_rejected(text: str) -> None:
    with pytest.raises(OptionError) as error:
        parse_option(text)
    assert error.value.code == "unknown_option"


def test_mutually_exclusive_options() -> None:
    kr_objectives = {"31": "3", "32": "3", "11": "1"}
    pairs = conflicting_pairs(
        [
            parse_option(i)
            for i in (
                "weekday_minutes:+60",
                "weekday_minutes:+90",
                "drop_kr:32",
                "defer_kr:32",
                "drop_objective:3",
                "defer_kr:11",
                "work_saturday",
            )
        ],
        kr_objectives,
    )
    assert {frozenset((a.id, b.id)) for a, b in pairs} == {
        frozenset(("weekday_minutes:+60", "weekday_minutes:+90")),
        frozenset(("drop_kr:32", "drop_objective:3")),
        frozenset(("drop_kr:32", "defer_kr:32")),
        frozenset(("drop_objective:3", "defer_kr:32")),
    }


def test_calendar_options_change_capacity_only() -> None:
    inp = make_input(make_task("a", 240), holidays=[HOLIDAY])
    both = apply_options(
        inp,
        [
            Option(OptionKind.weekday_minutes, minutes=60),
            Option(OptionKind.work_saturday),
            Option(OptionKind.work_holidays),
        ],
    )
    calendar = both.calendar
    assert calendar.weekday_capacity_minutes == (300, 300, 300, 300, 300, 240, 0)
    assert calendar.work_saturday and calendar.work_holidays and not calendar.work_sunday
    assert calendar.makeup_day_capacity_minutes == 300
    assert both.tasks == inp.tasks
    assert inp.calendar == CalendarConfig()


def test_weekday_extra_stops_at_the_maximum_working_day() -> None:
    inp = make_input(
        calendar=CalendarConfig(weekday_capacity_minutes=(600, 0, 240, 240, 240, 0, 0))
    )
    extra = apply_options(inp, [Option(OptionKind.weekday_minutes, minutes=180)])
    assert extra.calendar.weekday_capacity_minutes == (MAX_WORKDAY_MINUTES, 0, 420, 420, 420, 0, 0)


def test_dropping_scope_satisfies_dependencies_on_removed_tasks() -> None:
    first = make_task("a", 240, priority=1, kr_id="kr-a", objective_id="o1")
    second = make_task("b", 240, priority=2, kr_id="kr-b", objective_id="o2", deps=["a"])
    third = make_task("c", 240, priority=2, kr_id="kr-c", objective_id="o2")
    inp = make_input(first, second, third)

    without_a = apply_options(inp, [Option(OptionKind.drop_kr, target="kr-a")])
    assert [t.id for t in without_a.tasks] == ["b", "c"]
    assert "a" in without_a.done_task_ids
    assert {s.task_id for s in schedule(without_a).scheduled} == {"b", "c"}

    without_o2 = apply_options(inp, [Option(OptionKind.drop_objective, target="o2")])
    assert [t.id for t in without_o2.tasks] == ["a"]


def _overloaded() -> ScheduleInput:
    """65 working days of 4h (260h) against 318h of 4h/2h tasks, as in the S13 fixture."""
    tasks = [make_task(f"o1-{i:02d}", 240, priority=1, kr_id="kr11") for i in range(53)]
    tasks += [make_task(f"k31-{i:02d}", 240, priority=3, kr_id="kr31") for i in range(19)]
    tasks += [
        make_task(f"k32-{i:02d}", 240, priority=3, kr_order=2, kr_id="kr32") for i in range(7)
    ]
    tasks.append(make_task("k32-99", 120, priority=3, kr_order=2, kr_id="kr32"))
    return make_input(*tasks, holidays=vn_holidays())


def test_s13_numbers_for_single_options() -> None:
    inp = _overloaded()
    base = measure(inp, schedule(inp))
    assert (base.demand_minutes, base.supply_minutes) == (318 * 60, 260 * 60)
    assert (base.shortfall_minutes, base.late_task_count) == (58 * 60, 15)

    saturday = run_options(inp, [Option(OptionKind.work_saturday)])
    numbers = measure(inp, saturday)
    assert saturday.feasibility.status == "red"
    assert (numbers.supply_minutes, numbers.shortfall_minutes) == (312 * 60, 6 * 60)
    assert numbers.late_task_count == 2

    hour = run_options(inp, [Option(OptionKind.weekday_minutes, minutes=60)])
    numbers = measure(inp, hour)
    assert hour.feasibility.status == "yellow"
    assert (numbers.supply_minutes, numbers.buffer_minutes) == (325 * 60, 35 * 60)
    assert numbers.buffer_used_minutes == 28 * 60

    combined = run_options(
        inp, [Option(OptionKind.work_saturday), Option(OptionKind.defer_kr, target="kr32")]
    )
    numbers = measure(apply_options(inp, [Option(OptionKind.defer_kr, target="kr32")]), combined)
    assert combined.feasibility.status == "yellow"
    assert (numbers.demand_minutes, numbers.supply_minutes) == (288 * 60, 312 * 60)
    assert (numbers.buffer_minutes, numbers.buffer_used_minutes) == (32 * 60, 8 * 60)
    assert numbers.finish_date == date(2026, 12, 24)
    assert numbers.late_task_count == 0


def test_binary_search_finds_the_smallest_extra_hours() -> None:
    inp = _overloaded()
    enough = min_weekday_extra(inp, not_red)
    best = min_weekday_extra(inp, green)
    assert enough is not None and best is not None
    assert (enough.minutes, best.minutes) == (60, 90)
    assert best.result.feasibility.status == "green"
    below = run_options(inp, [Option(OptionKind.weekday_minutes, minutes=60)])
    assert below.feasibility.status == "yellow"


def test_binary_search_gives_up_when_even_twelve_hours_are_not_enough() -> None:
    inp = make_input(*[make_task(f"t{i}", 900) for i in range(80)])
    assert min_weekday_extra(inp, not_red) is None


@settings(max_examples=60, deadline=None)
@given(schedule_inputs(max_tasks=15), st.booleans())
def test_found_extra_is_accepted_and_one_step_less_is_not(
    inp: ScheduleInput, want_green: bool
) -> None:
    predicate = green if want_green else not_red
    found = min_weekday_extra(inp, predicate)
    if found is None:
        return
    assert predicate(found.result)
    options = [Option(OptionKind.weekday_minutes, minutes=found.minutes)] if found.minutes else []
    assert found.result == run_options(inp, options)
    assert_invariants(apply_options(inp, options), found.result)
    if found.minutes:
        smaller = found.minutes - WEEKDAY_STEP_MINUTES
        fewer = [Option(OptionKind.weekday_minutes, minutes=smaller)] if smaller else []
        assert not predicate(run_options(inp, fewer))
