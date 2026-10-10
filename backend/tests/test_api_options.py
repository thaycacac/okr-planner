"""Overload options over HTTP on the wave-2 S13 fixture: 318h of tasks against 260h.

Q4/2026 from 2026-10-01, Monday to Friday 4h, holiday 24/11. O1 (high) needs 212h; O3 (low)
has KR 3.1 with 76h and KR 3.2 with 30h (its 2h task last).
"""

import time
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.persistence.models import KeyResult, Objective, Quarter, Task, TaskDependency
from tests.api_support import ApiHarness
from tests.test_api_task_management import _quarter, _reschedule

H = 60


@dataclass(frozen=True)
class S13:
    quarter_id: int
    o1: int
    o3: int
    kr11: int
    kr31: int
    kr32: int


def _objective(api: ApiHarness, quarter_id: int, title: str, priority: str, krs: int) -> dict:
    body = {
        "title": title,
        "priority": priority,
        "key_results": [{"text": f"{title} KR {i + 1}", "kind": "binary"} for i in range(krs)],
    }
    response = api.client.post(f"/quarters/{quarter_id}/objectives", json=body)
    assert response.status_code == 201, response.text
    objective: dict = response.json()
    return objective


def _tasks(api: ApiHarness, kr_id: int, *minutes: int) -> list[int]:
    ids = []
    for i, estimate in enumerate(minutes):
        response = api.client.post(
            f"/key-results/{kr_id}/tasks",
            json={"title": f"Task {i + 1}", "estimate_minutes": estimate},
        )
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    return ids


def _s13(api: ApiHarness) -> S13:
    quarter_id = _quarter(api)
    o1 = _objective(api, quarter_id, "Onboarding SaaS", "high", 1)
    o3 = _objective(api, quarter_id, "Tự học", "low", 2)
    kr11 = o1["key_results"][0]["id"]
    kr31, kr32 = (kr["id"] for kr in o3["key_results"])
    _tasks(api, kr11, *[240] * 53)
    _tasks(api, kr31, *[240] * 19)
    _tasks(api, kr32, *[240] * 7, 120)
    _reschedule(api, quarter_id)
    return S13(quarter_id, o1["id"], o3["id"], kr11, kr31, kr32)


def _options(api: ApiHarness, quarter_id: int) -> dict[str, Any]:
    response = api.client.get(f"/quarters/{quarter_id}/options")
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def _evaluate(api: ApiHarness, quarter_id: int, *option_ids: str) -> Any:
    return api.client.post(
        f"/quarters/{quarter_id}/options/evaluate", json={"option_ids": list(option_ids)}
    )


def _apply(api: ApiHarness, quarter_id: int, key: str, *option_ids: str) -> Any:
    return api.client.post(
        f"/quarters/{quarter_id}/options/apply",
        json={"option_ids": list(option_ids)},
        headers={"Idempotency-Key": key},
    )


def _undo(api: ApiHarness, application_id: int) -> Any:
    return api.client.post(f"/option-applications/{application_id}/undo")


def _schedule(api: ApiHarness, quarter_id: int) -> dict[str, Any]:
    response = api.client.get(f"/quarters/{quarter_id}/schedule")
    assert response.status_code == 200, response.text
    schedule: dict[str, Any] = response.json()
    return schedule


def _red_warnings(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    return [w for w in schedule["warnings"] if w["level"] == "red"]


def _next_quarters(api: ApiHarness) -> list[dict[str, Any]]:
    quarters: list[dict[str, Any]] = api.client.get("/quarters?year=2027&number=1").json()
    return quarters


def _krs(api: ApiHarness, quarter_id: int, objective_id: int) -> list[dict[str, Any]]:
    detail = api.client.get(f"/quarters/{quarter_id}").json()
    objective = next(o for o in detail["objectives"] if o["id"] == objective_id)
    krs: list[dict[str, Any]] = objective["key_results"]
    return krs


# --- acceptance: every option has numbers ---------------------------------------------------


def test_every_option_of_an_overloaded_quarter_has_real_numbers(api: ApiHarness) -> None:
    s = _s13(api)
    before = _schedule(api, s.quarter_id)
    body = _options(api, s.quarter_id)

    assert body["overloaded"] is True
    current = body["current"]
    assert current["feasibility"]["status"] == "red"
    assert (current["feasibility"]["demand_minutes"], current["feasibility"]["supply_minutes"]) == (
        318 * H,
        260 * H,
    )
    assert (current["shortfall_minutes"], current["late_task_count"]) == (58 * H, 15)
    assert current["feasibility"]["late_key_result_ids"] == [s.kr31, s.kr32]

    options = {o["id"]: o for o in body["options"]}
    # (status, shortfall h, supply delta h, demand delta h)
    expected = {
        "weekday_minutes:+60": ("yellow", 0, 65, 0),
        "work_saturday": ("red", 6, 52, 0),
        "work_sunday": ("red", 6, 52, 0),
        "work_holidays": ("red", 54, 4, 0),
        f"drop_kr:{s.kr32}": ("red", 28, 0, -30),
        f"drop_objective:{s.o3}": ("green", 0, 0, -106),
        f"defer_kr:{s.kr31}": ("yellow", 0, 0, -76),
        f"defer_kr:{s.kr32}": ("red", 28, 0, -30),
    }
    assert set(options) == set(expected)
    for option_id, (status, shortfall, supply, demand) in expected.items():
        outcome = options[option_id]["outcome"]
        assert outcome["feasibility"]["status"] == status, option_id
        assert outcome["shortfall_minutes"] == shortfall * H, option_id
        assert outcome["supply_delta_minutes"] == supply * H, option_id
        assert outcome["demand_delta_minutes"] == demand * H, option_id
        assert outcome["resolves_overload"] == (status != "red"), option_id
        assert outcome["finish_date"] is not None, option_id
        assert outcome["feasibility"]["late_task_ids"] == [] or status == "red"

    weekday = options["weekday_minutes:+60"]["outcome"]
    assert (weekday["buffer_minutes"], weekday["buffer_used_minutes"]) == (35 * H, 28 * H)
    assert options[f"defer_kr:{s.kr31}"]["outcome"]["buffer_used_minutes"] == 10 * H
    assert options[f"drop_objective:{s.o3}"]["outcome"]["finish_date"] == "2026-12-15"
    assert options["work_saturday"]["outcome"]["late_task_count"] == 2
    assert body["weekday_hint"] == {
        "current_minutes": [240] * 5,
        "step_minutes": 30,
        "min_extra_minutes_not_red": 60,
        "min_extra_minutes_green": 90,
    }

    assert set(options[f"drop_kr:{s.kr32}"]["conflicts_with"]) == {
        f"drop_objective:{s.o3}",
        f"defer_kr:{s.kr32}",
    }
    assert options["work_saturday"]["conflicts_with"] == []
    assert options["work_saturday"]["group"] == "more_time"
    assert options[f"defer_kr:{s.kr31}"]["group"] == "defer"
    saturday = options["work_saturday"]["effects"][0]
    assert saturday["code"] == "quarter_calendar_changed"
    assert saturday["calendar"]["work_saturday"] is True
    assert saturday["calendar"]["capacity_minutes"]["sat"] == 240
    deferred = options[f"defer_kr:{s.kr32}"]["effects"][0]
    assert deferred["code"] == "key_result_deferred"
    assert (deferred["target_year"], deferred["target_number"]) == (2027, 1)
    assert deferred["target_quarter_exists"] is False
    assert deferred["task_count"] == 8

    after = _schedule(api, s.quarter_id)
    assert after["id"] == before["id"] and after["stale"] is False
    assert _next_quarters(api) == []


def test_evaluating_a_combination_runs_the_scheduler_once_more(api: ApiHarness) -> None:
    s = _s13(api)
    response = _evaluate(api, s.quarter_id, f"defer_kr:{s.kr32}", "work_saturday")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["option_ids"] == ["work_saturday", f"defer_kr:{s.kr32}"]
    assert body["before"]["feasibility"]["status"] == "red"
    after = body["after"]
    assert after["feasibility"]["status"] == "yellow"
    assert (after["feasibility"]["demand_minutes"], after["feasibility"]["supply_minutes"]) == (
        288 * H,
        312 * H,
    )
    assert (after["buffer_minutes"], after["buffer_used_minutes"]) == (32 * H, 8 * H)
    assert after["finish_date"] == "2026-12-24"
    assert after["late_task_count"] == 0 and after["resolves_overload"] is True
    assert [e["code"] for e in body["effects"]] == [
        "quarter_calendar_changed",
        "key_result_deferred",
    ]

    assert api.client.get(f"/quarters/{s.quarter_id}/calendar").json()["overridden"] is False
    assert [kr["id"] for kr in _krs(api, s.quarter_id, s.o3)] == [s.kr31, s.kr32]


def test_invalid_selections_are_rejected(api: ApiHarness) -> None:
    s = _s13(api)
    cases = [
        ([f"drop_kr:{s.kr32}", f"defer_kr:{s.kr32}"], "options_conflict"),
        ([f"drop_objective:{s.o3}", f"defer_kr:{s.kr31}"], "options_conflict"),
        (["weekday_minutes:+60", "weekday_minutes:+90"], "options_conflict"),
        (["ai_trim"], "unknown_option"),
        (["weekday_minutes:+0"], "unknown_option"),
        (["drop_kr:999999"], "option_not_applicable"),
    ]
    for option_ids, code in cases:
        response = _evaluate(api, s.quarter_id, *option_ids)
        assert response.status_code == 422, option_ids
        assert response.json()["detail"]["code"] == code, option_ids
        applied = _apply(api, s.quarter_id, f"key-{code}-{len(option_ids)}", *option_ids)
        assert applied.status_code == 422 and applied.json()["detail"]["code"] == code

    empty = _apply(api, s.quarter_id, "empty")
    assert empty.status_code == 422 and empty.json()["detail"]["code"] == "no_options"
    no_key = api.client.post(
        f"/quarters/{s.quarter_id}/options/apply", json={"option_ids": ["work_saturday"]}
    )
    assert no_key.status_code == 422
    assert api.client.get("/quarters/999999/options").status_code == 404
    assert _undo(api, 999999).status_code == 404
    assert api.client.get(f"/quarters/{s.quarter_id}/calendar").json()["overridden"] is False


# --- acceptance: applying an "enough" option really clears the red warnings -----------------


def test_applying_each_option_stores_exactly_the_evaluated_schedule(api: ApiHarness) -> None:
    s = _s13(api)
    body = _options(api, s.quarter_id)
    hint = body["weekday_hint"]["min_extra_minutes_not_red"]
    listed = {o["id"]: o["outcome"] for o in body["options"]}
    hinted = f"weekday_minutes:+{hint}"
    if hinted not in listed:
        listed[hinted] = _evaluate(api, s.quarter_id, hinted).json()["after"]
    assert any(o["resolves_overload"] for o in listed.values())

    for n, (option_id, outcome) in enumerate(sorted(listed.items())):
        response = _apply(api, s.quarter_id, f"each-{n}", option_id)
        assert response.status_code == 200, response.text
        application = response.json()
        schedule = application["schedule"]
        assert schedule == _schedule(api, s.quarter_id)
        assert schedule["stale"] is False
        assert schedule["feasibility"] == outcome["feasibility"], option_id
        assert application["after"] == outcome, option_id
        assert bool(_red_warnings(schedule)) != outcome["resolves_overload"], option_id

        undone = _undo(api, application["id"])
        assert undone.status_code == 200, undone.text
        restored = undone.json()["schedule"]
        assert restored["feasibility"] == body["current"]["feasibility"], option_id
        assert _red_warnings(restored)


def test_apply_saturdays_and_defer_then_undo(api: ApiHarness) -> None:
    s = _s13(api)
    global_calendar = api.client.get("/settings/calendar").json()
    evaluation = _evaluate(api, s.quarter_id, "work_saturday", f"defer_kr:{s.kr32}").json()

    response = _apply(api, s.quarter_id, "sat-defer", "work_saturday", f"defer_kr:{s.kr32}")
    assert response.status_code == 200, response.text
    application = response.json()
    assert application["option_ids"] == ["work_saturday", f"defer_kr:{s.kr32}"]
    assert application["after"] == evaluation["after"]
    assert application["effects"] == evaluation["effects"]
    assert application["undone_at"] is None
    schedule = application["schedule"]
    assert schedule["feasibility"]["status"] == "yellow"
    assert _red_warnings(schedule) == []

    calendar = api.client.get(f"/quarters/{s.quarter_id}/calendar").json()
    assert calendar["overridden"] is True
    assert calendar["settings"]["work_saturday"] is True
    assert calendar["settings"]["capacity_minutes"]["sat"] == 240
    assert api.client.get("/settings/calendar").json() == global_calendar

    assert [kr["id"] for kr in _krs(api, s.quarter_id, s.o3)] == [s.kr31]
    (next_quarter,) = _next_quarters(api)
    (moved_objective,) = api.client.get(f"/quarters/{next_quarter['id']}").json()["objectives"]
    assert (moved_objective["title"], moved_objective["priority"]) == ("Tự học", "low")
    (moved_kr,) = moved_objective["key_results"]
    assert moved_kr["id"] == s.kr32 and len(moved_kr["tasks"]) == 8

    replay = _apply(api, s.quarter_id, "sat-defer", f"defer_kr:{s.kr32}", "work_saturday")
    assert replay.status_code == 200
    assert replay.json()["id"] == application["id"]
    assert replay.json()["schedule"]["id"] == schedule["id"]
    reused = _apply(api, s.quarter_id, "sat-defer", "work_sunday")
    assert reused.status_code == 409
    assert reused.json()["detail"]["code"] == "idempotency_key_reused"

    undone = _undo(api, application["id"])
    assert undone.status_code == 200, undone.text
    restored = undone.json()
    assert restored["undone_at"] is not None
    assert restored["schedule"]["feasibility"]["status"] == "red"
    assert restored["schedule"]["feasibility"]["demand_minutes"] == 318 * H
    assert api.client.get(f"/quarters/{s.quarter_id}/calendar").json()["overridden"] is False
    assert [kr["id"] for kr in _krs(api, s.quarter_id, s.o3)] == [s.kr31, s.kr32]
    assert _next_quarters(api) == []

    again = _undo(api, application["id"])
    assert again.status_code == 200
    assert again.json()["undone_at"] == restored["undone_at"]
    assert again.json()["schedule"]["id"] == restored["schedule"]["id"]


def test_only_the_latest_application_can_be_undone(api: ApiHarness) -> None:
    s = _s13(api)
    custom = api.client.get("/settings/calendar").json()
    custom["capacity_minutes"]["mon"] = 300
    assert api.client.put(f"/quarters/{s.quarter_id}/calendar", json=custom).status_code == 200

    first = _apply(api, s.quarter_id, "first", "work_holidays").json()
    second = _apply(api, s.quarter_id, "second", f"drop_kr:{s.kr32}").json()
    assert _krs(api, s.quarter_id, s.o3)[1]["active"] is False
    assert s.kr32 not in {t["key_result_id"] for t in second["schedule"]["tasks"]}

    blocked = _undo(api, first["id"])
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "undo_not_latest"

    assert _undo(api, second["id"]).status_code == 200
    assert _krs(api, s.quarter_id, s.o3)[1]["active"] is True
    assert _undo(api, first["id"]).status_code == 200
    calendar = api.client.get(f"/quarters/{s.quarter_id}/calendar").json()
    assert calendar == {"quarter_id": s.quarter_id, "overridden": True, "settings": custom}


def test_deferring_into_an_existing_quarter_and_back_keeps_links_and_pins(
    api: ApiHarness,
) -> None:
    quarter_id = _quarter(api)
    high = _objective(api, quarter_id, "Ship", "high", 1)
    low = _objective(api, quarter_id, "Learn", "low", 1)
    (first,) = _tasks(api, high["key_results"][0]["id"], 240)
    kr_id = low["key_results"][0]["id"]
    linked, pinned = _tasks(api, kr_id, 240, 480)
    assert api.client.patch(f"/tasks/{linked}", json={"depends_on": [first]}).status_code == 200
    pin = api.client.put(f"/tasks/{pinned}/pin", json={"start_date": "2026-10-12"}).json()
    _reschedule(api, quarter_id)

    later = api.client.post("/quarters", json={"year": 2027, "number": 1}).json()["id"]
    existing = _objective(api, later, "Learn", "medium", 1)

    response = _apply(api, quarter_id, "defer", f"defer_kr:{kr_id}")
    assert response.status_code == 200, response.text
    effect = response.json()["effects"][0]
    assert effect["target_quarter_exists"] is True
    assert effect["pinned_task_ids"] == [pinned]
    assert [kr["id"] for kr in _krs(api, later, existing["id"])] == [
        existing["key_results"][0]["id"],
        kr_id,
    ]
    assert api.client.get(f"/tasks/{linked}").json()["depends_on"] == []
    assert api.client.get(f"/tasks/{pinned}").json()["pinned"] is False

    assert _undo(api, response.json()["id"]).status_code == 200
    assert [kr["id"] for kr in _krs(api, quarter_id, low["id"])] == [kr_id]
    assert [kr["id"] for kr in _krs(api, later, existing["id"])] == [
        existing["key_results"][0]["id"]
    ]
    assert api.client.get(f"/tasks/{linked}").json()["depends_on"] == [first]
    restored = api.client.get(f"/tasks/{pinned}").json()
    assert restored["pinned"] is True
    assert restored["pinned_allocations"] == pin["pinned_allocations"]


def test_a_dropped_key_result_can_be_reactivated(api: ApiHarness) -> None:
    s = _s13(api)
    assert _apply(api, s.quarter_id, "drop", f"drop_kr:{s.kr32}").status_code == 200
    assert api.client.patch(f"/key-results/{s.kr32}", json={"active": None}).status_code == 422
    reactivated = api.client.patch(f"/key-results/{s.kr32}", json={"active": True})
    assert reactivated.status_code == 200 and reactivated.json()["active"] is True
    assert _schedule(api, s.quarter_id)["stale"] is True
    refreshed = _reschedule(api, s.quarter_id)["schedule"]
    assert refreshed["feasibility"]["demand_minutes"] == 318 * H


# --- performance ----------------------------------------------------------------------------


def _seed_300_tasks(engine: Engine) -> int:
    """3 objectives x 2 KRs x 50 chained tasks, about 450h against 260h."""
    with Session(engine) as session:
        quarter = Quarter(year=2026, number=4)
        session.add(quarter)
        for o, priority in enumerate(("high", "medium", "low")):
            objective = Objective(quarter=quarter, title=f"O{o}", priority=priority, position=o)
            session.add(objective)
            for k in range(2):
                kr = KeyResult(objective=objective, text=f"KR{o}.{k}", kind="binary", position=k)
                session.add(kr)
                previous = None
                for t in range(50):
                    task = Task(
                        key_result=kr,
                        title=f"T{o}.{k}.{t}",
                        estimate_minutes=(60, 90, 120)[t % 3],
                        position=t,
                    )
                    session.add(task)
                    session.flush()
                    if previous is not None:
                        session.add(TaskDependency(task_id=task.id, depends_on_id=previous))
                    previous = task.id
        session.commit()
        return quarter.id


def test_options_for_300_tasks_answer_quickly(db_engine: Engine) -> None:
    quarter_id = _seed_300_tasks(db_engine)
    with ApiHarness.start(db_engine, today=date(2026, 10, 1)) as api:
        _reschedule(api, quarter_id)
        started = time.perf_counter()
        body = _options(api, quarter_id)
        listed = time.perf_counter() - started
        started = time.perf_counter()
        evaluated = _evaluate(api, quarter_id, "work_saturday", "work_sunday")
        evaluation = time.perf_counter() - started

    print(f"\n/options with 300 tasks: {listed:.3f}s, /options/evaluate: {evaluation:.3f}s")
    assert body["overloaded"] is True and len(body["options"]) >= 6
    assert evaluated.status_code == 200
    assert listed < 5 and evaluation < 5
