"""Manual task editing, pins and rescheduling over HTTP, without the LLM."""

from collections import defaultdict
from datetime import date
from typing import Any

import pytest
from sqlalchemy import Engine

from tests.api_support import ApiHarness

QUARTER = {"year": 2026, "number": 4}


def _quarter(api: ApiHarness) -> int:
    response = api.client.post("/quarters", json=QUARTER)
    assert response.status_code == 201, response.text
    quarter_id: int = response.json()["id"]
    return quarter_id


def _objective(
    api: ApiHarness, quarter_id: int, priority: str = "high", **kr: Any
) -> tuple[int, int]:
    body = {
        "title": f"Objective {priority}",
        "priority": priority,
        "key_results": [{"text": "Ship the work", "kind": "binary", **kr}],
    }
    response = api.client.post(f"/quarters/{quarter_id}/objectives", json=body)
    assert response.status_code == 201, response.text
    objective = response.json()
    return objective["id"], objective["key_results"][0]["id"]


def _task(api: ApiHarness, kr_id: int, minutes: int, depends_on: list[int] | None = None) -> int:
    response = api.client.post(
        f"/key-results/{kr_id}/tasks",
        json={
            "title": f"Task {minutes}",
            "estimate_minutes": minutes,
            "depends_on": depends_on or [],
        },
    )
    assert response.status_code == 201, response.text
    task_id: int = response.json()["id"]
    return task_id


def _reschedule(api: ApiHarness, quarter_id: int, **body: Any) -> dict[str, Any]:
    response = api.client.post(f"/quarters/{quarter_id}/reschedule", json=body)
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


def _by_task(schedule: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {t["task_id"]: t for t in schedule["tasks"]}


def _days(entry: dict[str, Any]) -> list[tuple[str, int]]:
    return [(a["date"], a["minutes"]) for a in entry["allocations"]]


# --- acceptance: pins survive rescheduling --------------------------------------------------


def test_reschedule_never_moves_pinned_tasks(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    first = _task(api, kr_id, 480)
    second = _task(api, kr_id, 240, [first])
    pinned = _task(api, kr_id, 600)

    pin = api.client.put(f"/tasks/{pinned}/pin", json={"start_date": "2026-10-12"})
    assert pin.status_code == 200, pin.text
    pinned_days = [(p["date"], p["minutes"]) for p in pin.json()["pinned_allocations"]]
    assert pinned_days == [("2026-10-12", 240), ("2026-10-13", 240), ("2026-10-14", 120)]

    result = _reschedule(api, quarter_id)
    assert result["applied"] and result["conflicts"] == []
    assert _days(_by_task(result["schedule"])[pinned]) == pinned_days

    # Growing the first task pushes its dependent later, but never the pin.
    grown = api.client.patch(f"/tasks/{first}", json={"estimate_minutes": 2400})
    assert grown.status_code == 200
    assert api.client.get(f"/quarters/{quarter_id}/schedule").json()["stale"] is True
    again = _reschedule(api, quarter_id)
    tasks = _by_task(again["schedule"])
    assert _days(tasks[pinned]) == pinned_days
    assert tasks[pinned]["pinned"] is True
    assert tasks[second]["start_date"] > tasks[first]["end_date"]
    assert {c["task_id"] for c in again["changes"]} == {first, second}
    assert again["schedule"]["stale"] is False


def test_pinning_where_scheduled_and_unpinning(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    task_id = _task(api, kr_id, 300)

    assert (
        api.client.put(f"/tasks/{task_id}/pin", json={}).json()["detail"]["code"]
        == "task_not_scheduled"
    )
    scheduled = _days(_by_task(_reschedule(api, quarter_id)["schedule"])[task_id])
    pinned = api.client.put(f"/tasks/{task_id}/pin", json={}).json()
    assert [(p["date"], p["minutes"]) for p in pinned["pinned_allocations"]] == scheduled

    unpinned = api.client.delete(f"/tasks/{task_id}/pin").json()
    assert unpinned["pinned"] is False and unpinned["pinned_allocations"] == []


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"start_date": "2026-10-03"}, "pin_non_working_day"),
        ({"start_date": "2027-01-04"}, "pin_outside_quarter"),
        ({"allocations": [{"date": "2026-10-05", "minutes": 100}]}, "pin_minutes_mismatch"),
        (
            {
                "allocations": [
                    {"date": "2026-10-05", "minutes": 100},
                    {"date": "2026-10-05", "minutes": 100},
                ]
            },
            "pin_duplicate_date",
        ),
    ],
)
def test_invalid_pins_are_rejected(api: ApiHarness, body: dict[str, Any], code: str) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    task_id = _task(api, kr_id, 200)
    response = api.client.put(f"/tasks/{task_id}/pin", json=body)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code


def test_over_capacity_pins_need_a_resolution(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    a = _task(api, kr_id, 200)
    b = _task(api, kr_id, 200)
    first = _reschedule(api, quarter_id)["schedule"]["id"]
    for task_id in (a, b):
        pin = {"allocations": [{"date": "2026-10-05", "minutes": 200}]}
        assert api.client.put(f"/tasks/{task_id}/pin", json=pin).status_code == 200

    preview = _reschedule(api, quarter_id, dry_run=True)
    assert preview["applied"] is False and preview["schedule"] is None
    assert preview["unresolved_task_ids"] == [a, b]
    conflict = preview["conflicts"][0]
    assert conflict["code"] == "pinned_over_capacity"
    assert (conflict["capacity_minutes"], conflict["pinned_minutes"]) == (240, 400)
    assert conflict["related_task_ids"] == [b]
    assert "unlink" not in conflict["allowed_actions"]

    # Unresolved conflicts leave the stored schedule untouched.
    assert _reschedule(api, quarter_id)["applied"] is False
    assert api.client.get(f"/quarters/{quarter_id}/schedule").json()["id"] == first

    resolved = _reschedule(
        api,
        quarter_id,
        resolutions=[{"task_id": a, "action": "keep"}, {"task_id": b, "action": "unpin"}],
    )
    assert resolved["applied"] is True
    tasks = _by_task(resolved["schedule"])
    assert _days(tasks[a]) == [("2026-10-05", 200)]
    assert tasks[b]["pinned"] is False
    assert api.client.get(f"/tasks/{b}").json()["pinned"] is False
    assert api.client.get(f"/tasks/{a}").json()["pinned"] is True


def test_repin_moves_the_pin_to_the_earliest_valid_days(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    a = _task(api, kr_id, 240)
    b = _task(api, kr_id, 240)
    for task_id in (a, b):
        pin = {"allocations": [{"date": "2026-10-06", "minutes": 240}]}
        api.client.put(f"/tasks/{task_id}/pin", json=pin)
    result = _reschedule(
        api,
        quarter_id,
        resolutions=[{"task_id": a, "action": "keep"}, {"task_id": b, "action": "repin"}],
    )
    assert result["applied"] is True
    repinned = api.client.get(f"/tasks/{b}").json()
    assert repinned["pinned"] is True
    assert repinned["pinned_allocations"] == [{"date": "2026-10-01", "minutes": 240}]


def test_dependency_conflict_can_be_unlinked(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    before = _task(api, kr_id, 480)
    after = _task(api, kr_id, 240, [before])
    api.client.put(f"/tasks/{after}/pin", json={"start_date": "2026-10-01"})

    preview = _reschedule(api, quarter_id, dry_run=True)
    [conflict] = preview["conflicts"]
    assert conflict["code"] == "pinned_dependency_conflict"
    assert (conflict["task_id"], conflict["related_task_ids"]) == (after, [before])
    assert "unlink" in conflict["allowed_actions"]
    # A dry run must not store the unlink either.
    assert api.client.get(f"/tasks/{after}").json()["depends_on"] == [before]

    result = _reschedule(api, quarter_id, resolutions=[{"task_id": after, "action": "unlink"}])
    assert result["applied"] is True and result["conflicts"] == []
    assert api.client.get(f"/tasks/{after}").json()["depends_on"] == []


# --- acceptance: several OKRs share one capacity --------------------------------------------


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_several_objectives_never_exceed_daily_capacity(api: ApiHarness, seed: int) -> None:
    quarter_id = _quarter(api)
    objectives = {}
    for priority in ("low", "high", "medium"):
        objective_id, kr_id = _objective(api, quarter_id, priority)
        objectives[objective_id] = priority
        previous: list[int] = []
        for i in range(4):
            minutes = 60 + (seed * 97 + i * 131 + len(priority) * 29) % 600
            previous = [_task(api, kr_id, minutes, previous[-1:] if i % 2 else [])]
    paused_id, paused_kr = _objective(api, quarter_id, "high")
    paused_task = _task(api, paused_kr, 480)
    api.client.patch(f"/objectives/{paused_id}", json={"active": False})

    schedule = _reschedule(api, quarter_id)["schedule"]
    load: dict[str, int] = defaultdict(int)
    for task in schedule["tasks"]:
        for allocation in task["allocations"]:
            load[allocation["date"]] += allocation["minutes"]
    capacity = {d["date"]: d["capacity_minutes"] for d in schedule["days"]}
    assert load and all(minutes <= capacity[day] for day, minutes in load.items())
    assert all(d["scheduled_minutes"] <= d["capacity_minutes"] for d in schedule["days"])
    assert paused_task not in _by_task(schedule)

    finish: dict[str, str] = {}
    for task in schedule["tasks"]:
        priority = objectives[task["objective_id"]]
        finish[priority] = max(finish.get(priority, ""), task["end_date"])
    assert finish["high"] <= finish["medium"] <= finish["low"]


# --- acceptance: KR milestones --------------------------------------------------------------


def test_kr_milestones_rise_to_the_target_when_the_schedule_ends(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id, kind="numeric", baseline=10, target=50, unit="%")
    for minutes in (600, 900, 480):
        _task(api, kr_id, minutes)
    _reschedule(api, quarter_id)

    [kr] = api.client.get(f"/quarters/{quarter_id}/kr-milestones").json()
    assert kr["key_result_id"] == kr_id
    assert kr["total_minutes"] == kr["planned_minutes"] == 1980
    for series in (kr["weekly"], kr["monthly"]):
        values = [c["expected_value"] for c in series]
        assert values == sorted(values)
        assert values[0] >= 10 and values[-1] == 50
    finish = kr["expected_completion_date"]
    reached = [c for c in kr["weekly"] if c["period_end"] >= finish]
    assert all(c["expected_value"] == 50 for c in reached)
    assert all(c["expected_value"] < 50 for c in kr["weekly"] if c["period_end"] < finish)


def test_kr_milestones_survive_a_stale_schedule_after_an_estimate_is_lowered(
    api: ApiHarness,
) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id, kind="numeric", baseline=0, target=100)
    lowered = _task(api, kr_id, 960)
    _task(api, kr_id, 480)
    _reschedule(api, quarter_id)
    edited = api.client.patch(f"/tasks/{lowered}", json={"estimate_minutes": 120})
    assert edited.status_code == 200
    assert api.client.get(f"/quarters/{quarter_id}/schedule").json()["stale"] is True

    response = api.client.get(f"/quarters/{quarter_id}/kr-milestones")
    assert response.status_code == 200, response.text
    [kr] = response.json()
    assert kr["total_minutes"] == kr["planned_minutes"] == 600
    for series in (kr["weekly"], kr["monthly"]):
        assert all(0 <= c["progress"] <= 1 for c in series)
        assert all(c["completed_minutes"] <= 600 for c in series)
        assert series[-1]["progress"] == 1 and series[-1]["expected_value"] == 100


def test_kr_milestones_skip_paused_objectives_and_text_krs_have_no_value(
    api: ApiHarness,
) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    paused, _ = _objective(api, quarter_id, "low")
    api.client.patch(f"/objectives/{paused}", json={"active": False})
    _task(api, kr_id, 120)

    [kr] = api.client.get(f"/quarters/{quarter_id}/kr-milestones").json()
    assert kr["key_result_id"] == kr_id
    assert kr["planned_minutes"] == 0
    assert all(c["expected_value"] is None for c in kr["weekly"])


# --- task editing ---------------------------------------------------------------------------


def test_task_crud_and_dependency_rules(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    _, other_kr = _objective(api, quarter_id, "low")
    a = _task(api, kr_id, 60)
    b = _task(api, kr_id, 60, [a])
    c = _task(api, kr_id, 60, [b])

    created = api.client.get(f"/tasks/{c}").json()
    assert created["user_edited"] is True and created["position"] == 2

    cycle = api.client.patch(f"/tasks/{a}", json={"depends_on": [c]})
    assert cycle.status_code == 422
    assert cycle.json()["detail"]["code"] == "dependency_cycle"
    assert f"{a} -> {c} -> {b} -> {a}" in cycle.json()["detail"]["message"]
    assert api.client.patch(f"/tasks/{a}", json={"depends_on": [a]}).json()["detail"]["code"] == (
        "dependency_on_itself"
    )
    assert api.client.patch(f"/tasks/{a}", json={"depends_on": [999]}).json()["detail"]["code"] == (
        "unknown_dependency"
    )
    assert api.client.patch(f"/tasks/{a}", json={"title": None}).status_code == 422

    moved = api.client.patch(
        f"/tasks/{c}", json={"key_result_id": other_kr, "title": " Renamed ", "position": 7}
    ).json()
    assert (moved["key_result_id"], moved["title"], moved["position"]) == (other_kr, "Renamed", 7)

    done = api.client.patch(f"/tasks/{a}", json={"status": "done"}).json()
    assert done["status"] == "done" and done["completed_at"] is not None
    assert api.client.put(f"/tasks/{a}/pin", json={}).json()["detail"]["code"] == "task_done"
    reopened = api.client.patch(f"/tasks/{a}", json={"status": "todo"}).json()
    assert reopened["completed_at"] is None

    assert api.client.delete(f"/tasks/{a}?with_dependents=true").status_code == 204
    for task_id in (a, b, c):
        assert api.client.get(f"/tasks/{task_id}").status_code == 404


def test_deleting_a_task_keeps_its_dependents_by_default(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    a = _task(api, kr_id, 60)
    b = _task(api, kr_id, 60, [a])
    assert api.client.delete(f"/tasks/{a}").status_code == 204
    assert api.client.get(f"/tasks/{b}").json()["depends_on"] == []


def test_tasks_cannot_cross_quarters(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    other = api.client.post("/quarters", json={"year": 2027, "number": 1}).json()["id"]
    _, far_kr = _objective(api, other)
    far_task = _task(api, far_kr, 60)
    task_id = _task(api, kr_id, 60)

    move = api.client.patch(f"/tasks/{task_id}", json={"key_result_id": far_kr})
    assert move.json()["detail"]["code"] == "key_result_not_in_quarter"
    link = api.client.patch(f"/tasks/{task_id}", json={"depends_on": [far_task]})
    assert link.json()["detail"]["code"] == "unknown_dependency"


def test_changing_the_estimate_refills_the_pin(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    task_id = _task(api, kr_id, 240)
    api.client.put(f"/tasks/{task_id}/pin", json={"start_date": "2026-10-09"})
    grown = api.client.patch(f"/tasks/{task_id}", json={"estimate_minutes": 300}).json()
    assert grown["pinned_allocations"] == [
        {"date": "2026-10-09", "minutes": 240},
        {"date": "2026-10-12", "minutes": 60},
    ]


def test_finished_tasks_keep_their_history(db_engine: Engine) -> None:
    with ApiHarness.start(db_engine, today=date(2026, 10, 1)) as api:
        quarter_id = _quarter(api)
        _, kr_id = _objective(api, quarter_id)
        done_id = _task(api, kr_id, 480)
        open_id = _task(api, kr_id, 240)
        _reschedule(api, quarter_id)
    with ApiHarness.start(db_engine, today=date(2026, 10, 15)) as api:
        api.client.patch(f"/tasks/{done_id}", json={"status": "done"})
        schedule = _reschedule(api, quarter_id)["schedule"]
        tasks = _by_task(schedule)
        assert tasks[done_id]["done"] is True
        assert _days(tasks[done_id]) == [("2026-10-01", 240), ("2026-10-02", 240)]
        assert tasks[open_id]["start_date"] == "2026-10-15"
        assert schedule["feasibility"]["demand_minutes"] == 240


# --- quarters -------------------------------------------------------------------------------


def test_quarters_filter_and_previous(api: ApiHarness) -> None:
    ids = {}
    for year, number in ((2026, 2), (2026, 4), (2027, 1)):
        response = api.client.post("/quarters", json={"year": year, "number": number})
        ids[(year, number)] = response.json()["id"]

    in_2026 = api.client.get("/quarters", params={"year": 2026}).json()
    assert [q["number"] for q in in_2026] == [2, 4]
    assert [q["id"] for q in api.client.get("/quarters?year=2027&number=1").json()] == [
        ids[(2027, 1)]
    ]

    previous = api.client.get(f"/quarters/{ids[(2027, 1)]}/previous").json()
    assert (previous["year"], previous["number"]) == (2026, 4)
    assert api.client.get(f"/quarters/{ids[(2026, 4)]}/previous").json()["number"] == 2
    first = api.client.get(f"/quarters/{ids[(2026, 2)]}/previous")
    assert first.status_code == 404 and first.json()["detail"]["code"] == "no_previous_quarter"


def test_deleting_a_quarter_removes_its_data(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    task_id = _task(api, kr_id, 240)
    api.client.put(f"/tasks/{task_id}/pin", json={"start_date": "2026-10-05"})
    _reschedule(api, quarter_id)
    api.client.put(
        f"/quarters/{quarter_id}/calendar",
        json=api.client.get("/settings/calendar").json(),
    )

    assert api.client.delete(f"/quarters/{quarter_id}").status_code == 204
    assert api.client.get(f"/tasks/{task_id}").status_code == 404
    assert api.client.get(f"/quarters/{quarter_id}/schedule").status_code == 404
    assert api.client.get("/quarters").json() == []


def test_plan_start_moves_the_first_scheduled_day(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    _, kr_id = _objective(api, quarter_id)
    task_id = _task(api, kr_id, 240)
    before = _by_task(_reschedule(api, quarter_id)["schedule"])[task_id]

    # Pick a start 10+ days after the current first day, then check the plan begins there.
    first = date.fromisoformat(before["start_date"])
    target = date.fromordinal(first.toordinal() + 10)
    updated = api.client.put(
        f"/quarters/{quarter_id}/plan-start", json={"plan_start": target.isoformat()}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["plan_start"] == target.isoformat()

    schedule = api.client.get(f"/quarters/{quarter_id}/schedule").json()
    assert schedule["stale"] is True
    after = _by_task(_reschedule(api, quarter_id)["schedule"])[task_id]
    assert date.fromisoformat(after["start_date"]) >= target

    assert (
        api.client.put(f"/quarters/{quarter_id}/plan-start", json={"plan_start": None}).json()[
            "plan_start"
        ]
        is None
    )


def test_plan_start_must_be_inside_the_quarter(api: ApiHarness) -> None:
    quarter_id = _quarter(api)
    response = api.client.put(
        f"/quarters/{quarter_id}/plan-start", json={"plan_start": "2026-09-30"}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "plan_start_outside_quarter"
