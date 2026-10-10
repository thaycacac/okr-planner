"""Acceptance criterion 1: no task lands on a Saturday, Sunday or public holiday while that
kind of day is switched off; switching it on schedules work there.

Q4/2026 from 2026-10-01 with the bundled holiday 2026-11-24 (Tuesday). Two objectives with
four KRs of ten 6-hour tasks each: 240 hours, enough to run past the holiday either way.
"""

from tests.acceptance.support import (
    FOUR_HOURS,
    PlanLLM,
    allocation_days,
    assert_schedule_invariants,
    calendar_body,
    create_objective,
    create_quarter,
    holidays_in,
    plan_quarter,
    reschedule,
    schedule_of,
    set_global_calendar,
    set_quarter_calendar,
    tasks_of,
    weekday_of,
)
from tests.api_support import ApiHarness

HOLIDAY = "2026-11-24"
SATURDAY, SUNDAY = 5, 6
WEEKEND_CAPACITY = {**FOUR_HOURS, "sat": 240, "sun": 240}


def _planned_quarter(api: ApiHarness) -> int:
    api.provider.handler = PlanLLM(tasks_per_kr=10, hours=6)
    quarter_id = create_quarter(api)
    create_objective(
        api,
        quarter_id,
        "Ra mắt gói Team cho sản phẩm",
        "high",
        ["Hoàn thành thanh toán theo năm", "Viết tài liệu hướng dẫn gói Team"],
    )
    create_objective(
        api,
        quarter_id,
        "Nâng cao chất lượng hỗ trợ khách hàng",
        "medium",
        ["Xây dựng bộ câu trả lời mẫu", "Đào tạo nhân viên hỗ trợ mới"],
    )
    plan_quarter(api, quarter_id)
    return quarter_id


def test_switched_off_weekends_and_holidays_get_no_work_even_with_capacity(
    api: ApiHarness,
) -> None:
    set_global_calendar(api, calendar_body(WEEKEND_CAPACITY))
    quarter_id = _planned_quarter(api)
    schedule = schedule_of(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    used = allocation_days(schedule)
    assert HOLIDAY in holidays_in(api, 2026)
    assert max(used) > HOLIDAY, "the plan must run past the holiday to prove it was skipped"
    assert HOLIDAY not in used
    assert all(weekday_of(day) < SATURDAY for day in used)
    assert schedule["unscheduled"] == []

    days = {d["date"]: d for d in schedule["days"]}
    assert (days["2026-10-03"]["off_reason"], days["2026-10-04"]["off_reason"]) == (
        "weekend",
        "weekend",
    )
    assert days[HOLIDAY]["off_reason"] == "holiday"
    for day in days.values():
        if day["off_reason"] is not None:
            assert (day["capacity_minutes"], day["scheduled_minutes"]) == (0, 0), day


def test_switching_weekends_and_holidays_on_schedules_work_on_them(api: ApiHarness) -> None:
    quarter_id = _planned_quarter(api)
    set_quarter_calendar(
        api, quarter_id, calendar_body(WEEKEND_CAPACITY, saturday=True, sunday=True, holidays=True)
    )
    schedule = reschedule(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    days = {d["date"]: d for d in schedule["days"]}
    for day in ("2026-10-03", "2026-10-04", HOLIDAY):
        assert days[day]["off_reason"] is None, day
        assert days[day]["capacity_minutes"] == 240, day
        assert days[day]["scheduled_minutes"] == 240, day
    used = allocation_days(schedule)
    assert {weekday_of(day) for day in used} == set(range(7))


def test_each_switch_only_opens_its_own_kind_of_day(api: ApiHarness) -> None:
    quarter_id = _planned_quarter(api)
    set_quarter_calendar(api, quarter_id, calendar_body(WEEKEND_CAPACITY, saturday=True))
    schedule = reschedule(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    used = allocation_days(schedule)
    assert any(weekday_of(day) == SATURDAY for day in used)
    assert not any(weekday_of(day) == SUNDAY for day in used)
    assert max(used) > HOLIDAY and HOLIDAY not in used


def test_leave_days_get_no_work(api: ApiHarness) -> None:
    quarter_id = _planned_quarter(api)
    created = api.client.post(
        "/calendar/leave-days", json={"start_date": "2026-10-05", "end_date": "2026-10-06"}
    )
    assert created.status_code == 201, created.text
    schedule = reschedule(api, quarter_id)
    assert_schedule_invariants(schedule, tasks_of(api, quarter_id))

    days = {d["date"]: d for d in schedule["days"]}
    for day in ("2026-10-05", "2026-10-06"):
        assert days[day]["off_reason"] == "leave"
        assert days[day]["scheduled_minutes"] == 0
    assert {"2026-10-02", "2026-10-07"} <= allocation_days(schedule)
