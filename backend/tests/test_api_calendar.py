"""Per-quarter calendar override, leave days and holiday editing over HTTP."""

from typing import Any

from tests.api_support import ApiHarness


def _code(response: Any) -> str:
    code: str = response.json()["detail"]["code"]
    return code


def _planned_quarter(api: ApiHarness) -> tuple[int, int]:
    quarter_id = api.client.post("/quarters", json={"year": 2026, "number": 4}).json()["id"]
    objective = api.client.post(
        f"/quarters/{quarter_id}/objectives",
        json={"title": "Ship", "priority": "high", "key_results": [{"text": "Launch"}]},
    ).json()
    kr_id = objective["key_results"][0]["id"]
    task = api.client.post(
        f"/key-results/{kr_id}/tasks", json={"title": "Work", "estimate_minutes": 480}
    )
    assert task.status_code == 201, task.text
    reschedule = api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert reschedule.json()["applied"] is True
    task_id: int = task.json()["id"]
    return quarter_id, task_id


def _days_of(api: ApiHarness, quarter_id: int, task_id: int) -> list[str]:
    schedule = api.client.get(f"/quarters/{quarter_id}/schedule").json()
    [task] = [t for t in schedule["tasks"] if t["task_id"] == task_id]
    return [a["date"] for a in task["allocations"]]


def test_leave_days_skip_days_off_and_move_the_schedule(api: ApiHarness) -> None:
    quarter_id, task_id = _planned_quarter(api)
    assert _days_of(api, quarter_id, task_id) == ["2026-10-01", "2026-10-02"]

    created = api.client.post(
        "/calendar/leave-days",
        json={"start_date": "2026-10-01", "end_date": "2026-10-05", "note": "Nghỉ phép"},
    )
    assert created.status_code == 201
    assert [d["date"] for d in created.json()] == ["2026-10-01", "2026-10-02", "2026-10-05"]
    again = api.client.post("/calendar/leave-days", json={"start_date": "2026-10-02"})
    assert again.status_code == 201 and again.json() == []

    listed = api.client.get("/calendar/leave-days", params={"year": 2026}).json()
    assert [d["note"] for d in listed] == ["Nghỉ phép"] * 3
    assert api.client.get("/calendar/leave-days", params={"year": 2027}).json() == []

    schedule = api.client.get(f"/quarters/{quarter_id}/schedule").json()
    assert schedule["stale"] is True
    api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert _days_of(api, quarter_id, task_id) == ["2026-10-06", "2026-10-07"]

    assert api.client.delete(f"/calendar/leave-days/{listed[0]['id']}").status_code == 204
    assert api.client.delete(f"/calendar/leave-days/{listed[0]['id']}").status_code == 404


def test_leave_range_is_validated(api: ApiHarness) -> None:
    backwards = {"start_date": "2026-10-05", "end_date": "2026-10-01"}
    assert api.client.post("/calendar/leave-days", json=backwards).status_code == 422
    too_long = {"start_date": "2026-01-01", "end_date": "2026-12-31"}
    assert api.client.post("/calendar/leave-days", json=too_long).status_code == 422


def test_quarter_calendar_override(api: ApiHarness) -> None:
    quarter_id, task_id = _planned_quarter(api)
    inherited = api.client.get(f"/quarters/{quarter_id}/calendar").json()
    assert inherited["overridden"] is False
    assert inherited["settings"] == api.client.get("/settings/calendar").json()

    settings = inherited["settings"]
    settings["capacity_minutes"] = {**settings["capacity_minutes"], "thu": 480}
    override = api.client.put(f"/quarters/{quarter_id}/calendar", json=settings).json()
    assert override["overridden"] is True
    assert override["settings"]["capacity_minutes"]["thu"] == 480
    assert api.client.get("/settings/calendar").json()["capacity_minutes"]["thu"] == 240

    api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert _days_of(api, quarter_id, task_id) == ["2026-10-01"]

    reset = api.client.delete(f"/quarters/{quarter_id}/calendar").json()
    assert reset["overridden"] is False
    assert api.client.get(f"/quarters/{quarter_id}/schedule").json()["stale"] is True
    assert api.client.get("/quarters/999/calendar").status_code == 404


def test_holidays_can_be_added_edited_and_reset(api: ApiHarness) -> None:
    defaults = api.client.get("/calendar/holidays", params={"year": 2026}).json()
    assert defaults and not any(h["custom"] for h in defaults)

    quarter_id, task_id = _planned_quarter(api)
    added = api.client.post(
        "/calendar/holidays",
        json={"date": "2026-10-01", "kind": "personal_day_off", "name_vi": "Nghỉ riêng"},
    )
    assert added.status_code == 201
    holiday = added.json()
    assert holiday["custom"] is True and holiday["name_en"] == "Nghỉ riêng"
    duplicate = api.client.post(
        "/calendar/holidays",
        json={"date": "2026-10-01", "kind": "public_holiday", "name_vi": "Trùng"},
    )
    assert duplicate.status_code == 409 and _code(duplicate) == "holiday_exists"

    api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert _days_of(api, quarter_id, task_id) == ["2026-10-02", "2026-10-05"]

    official = defaults[0]
    moved = api.client.patch(
        f"/calendar/holidays/{official['id']}", json={"name_en": "Edited"}
    ).json()
    assert moved["custom"] is True and moved["name_en"] == "Edited"
    clash = api.client.patch(f"/calendar/holidays/{official['id']}", json={"date": "2026-10-01"})
    assert clash.status_code == 409

    restored = api.client.post("/calendar/holidays/reset", params={"year": 2026}).json()
    assert [(h["date"], h["name_en"]) for h in restored] == [
        (h["date"], h["name_en"]) for h in defaults
    ]
    assert not any(h["custom"] for h in restored)
    missing = api.client.post("/calendar/holidays/reset", params={"year": 2099})
    assert missing.status_code == 404 and _code(missing) == "holiday_data_missing"

    deleted = api.client.delete(f"/calendar/holidays/{restored[0]['id']}")
    assert deleted.status_code == 204
    assert len(api.client.get("/calendar/holidays?year=2026").json()) == len(defaults) - 1


def test_makeup_day_adds_a_working_day(api: ApiHarness) -> None:
    quarter_id, task_id = _planned_quarter(api)
    api.client.post(
        "/calendar/leave-days", json={"start_date": "2026-10-01", "end_date": "2026-10-02"}
    )
    api.client.post(
        "/calendar/holidays",
        json={"date": "2026-10-03", "kind": "makeup_day", "name_vi": "Làm bù"},
    )
    api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert _days_of(api, quarter_id, task_id) == ["2026-10-03", "2026-10-05"]
