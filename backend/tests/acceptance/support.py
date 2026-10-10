"""Scenario builders and invariant checks shared by the acceptance suite.

Every scenario goes through the HTTP API with ``FakeProvider``; nothing touches the network.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from itertools import pairwise
from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.fake import FakeReply
from app.planner_llm.schemas import KeyResultCheck, KeyResultNeedsOutput
from tests.api_support import ApiHarness, llm_task

Json = dict[str, Any]
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
FOUR_HOURS = {day: 240 if day not in ("sat", "sun") else 0 for day in WEEKDAYS}


@dataclass
class PlanLLM:
    """A clear OKR: clarify accepts, each KR gets ``tasks_per_kr`` tasks of ``hours`` each
    (chained when ``chain``), and dedup links the first task of every KR after the first to
    the last task of the previous KR of the same objective when ``cross_kr``.

    ``tasks_by_kr`` and ``hours_by_kr`` override the counts per prompt KR id (``kr<id>``).
    """

    tasks_per_kr: int = 2
    hours: float = 4
    chain: bool = True
    cross_kr: bool = False
    tasks_by_kr: dict[str, int] = field(default_factory=dict)
    hours_by_kr: dict[str, float] = field(default_factory=dict)

    def __call__(self, prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if schema is KeyResultCheck:
            return {"end_result": "done", "concrete": True}
        if schema is KeyResultNeedsOutput:
            return {"needs": []}
        if prompt.step == "decompose":
            assert prompt.kr_id is not None
            hours = self.hours_by_kr.get(prompt.kr_id, self.hours)
            count = self.tasks_by_kr.get(prompt.kr_id, self.tasks_per_kr)
            tasks = []
            for i in range(1, count + 1):
                deps = [f"t{i - 1}"] if self.chain and i > 1 else []
                tasks.append(llm_task(f"t{i}", prompt.kr_id, hours, deps))
            return {"tasks": tasks}
        if prompt.step == "dedup":
            return {"merges": [], "cross_dependencies": self._cross(prompt)}
        return {"ok": True}

    def _cross(self, prompt: Prompt) -> list[Json]:
        if not self.cross_kr or prompt.attempt:
            return []
        payload = json.loads(prompt.user)
        by_kr: dict[str, list[str]] = defaultdict(list)
        for task in payload["tasks"]:
            by_kr[task["kr_id"]].append(task["id"])
        by_objective: dict[str, list[str]] = defaultdict(list)
        for kr in payload["key_results"]:
            by_objective[kr["objective_id"]].append(kr["id"])
        return [
            {"task_id": by_kr[later][0], "depends_on_id": by_kr[earlier][-1], "reason": "order"}
            for krs in by_objective.values()
            for earlier, later in pairwise(krs)
        ]


def create_quarter(api: ApiHarness, year: int = 2026, number: int = 4) -> int:
    response = api.client.post("/quarters", json={"year": year, "number": number})
    assert response.status_code == 201, response.text
    quarter_id: int = response.json()["id"]
    return quarter_id


def create_objective(
    api: ApiHarness,
    quarter_id: int,
    title: str,
    priority: str,
    key_results: list[str | Json],
) -> Json:
    krs = [{"text": kr, "kind": "binary"} if isinstance(kr, str) else kr for kr in key_results]
    response = api.client.post(
        f"/quarters/{quarter_id}/objectives",
        json={"title": title, "priority": priority, "key_results": krs},
    )
    assert response.status_code == 201, response.text
    objective: Json = response.json()
    return objective


def create_task(
    api: ApiHarness, kr_id: int, minutes: int, depends_on: list[int] | None = None
) -> int:
    response = api.client.post(
        f"/key-results/{kr_id}/tasks",
        json={"title": f"Task {minutes}m", "estimate_minutes": minutes, "depends_on": depends_on},
    )
    assert response.status_code == 201, response.text
    task_id: int = response.json()["id"]
    return task_id


def run_plan(api: ApiHarness, path: str = "/plans", **body: Any) -> tuple[str, list[Json]]:
    """Starts a plan job and returns its id with every progress event up to the end."""
    response = api.client.post(path, json=body)
    assert response.status_code == 202, response.text
    job_id: str = response.json()["job_id"]
    return job_id, api.events(job_id)


def plan_quarter(api: ApiHarness, quarter_id: int) -> Json:
    job_id, events = run_plan(api, quarter_id=quarter_id, skip_clarification=True)
    assert events[-1]["run_status"] == "succeeded", events[-1]
    run: Json = api.client.get(f"/plans/{job_id}").json()
    return run


def schedule_of(api: ApiHarness, quarter_id: int) -> Json:
    response = api.client.get(f"/quarters/{quarter_id}/schedule")
    assert response.status_code == 200, response.text
    schedule: Json = response.json()
    return schedule


def tasks_of(api: ApiHarness, quarter_id: int) -> list[Json]:
    response = api.client.get(f"/quarters/{quarter_id}/tasks")
    assert response.status_code == 200, response.text
    tasks: list[Json] = response.json()
    return tasks


def reschedule(api: ApiHarness, quarter_id: int) -> Json:
    response = api.client.post(f"/quarters/{quarter_id}/reschedule", json={})
    assert response.status_code == 200, response.text
    result: Json = response.json()
    assert result["applied"] is True, result
    schedule: Json = result["schedule"]
    return schedule


def calendar_body(
    capacity: dict[str, int] | None = None,
    *,
    saturday: bool = False,
    sunday: bool = False,
    holidays: bool = False,
) -> Json:
    return {
        "capacity_minutes": capacity or FOUR_HOURS,
        "work_saturday": saturday,
        "work_sunday": sunday,
        "work_holidays": holidays,
    }


def set_global_calendar(api: ApiHarness, body: Json) -> None:
    response = api.client.put("/settings/calendar", json=body)
    assert response.status_code == 200, response.text


def set_quarter_calendar(api: ApiHarness, quarter_id: int, body: Json) -> None:
    response = api.client.put(f"/quarters/{quarter_id}/calendar", json=body)
    assert response.status_code == 200, response.text


def holidays_in(api: ApiHarness, year: int) -> set[str]:
    rows = api.client.get("/calendar/holidays", params={"year": year}).json()
    return {r["date"] for r in rows if r["kind"] != "makeup_day"}


def allocation_days(schedule: Json) -> set[str]:
    return {a["date"] for t in schedule["tasks"] for a in t["allocations"]}


def load_by_day(schedule: Json) -> dict[str, int]:
    load: dict[str, int] = defaultdict(int)
    for task in schedule["tasks"]:
        for allocation in task["allocations"]:
            load[allocation["date"]] += allocation["minutes"]
    return dict(load)


def weekday_of(day: str) -> int:
    return date.fromisoformat(day).weekday()


def assert_schedule_invariants(schedule: Json, tasks: list[Json]) -> None:
    """Checks every hard rule of a stored schedule against the tasks it was built from."""
    by_id = {t["id"]: t for t in tasks}
    days = {d["date"]: d for d in schedule["days"]}
    placed = {t["task_id"]: t for t in schedule["tasks"]}
    unscheduled = {u["task_id"] for u in schedule["unscheduled"]}
    window = (schedule["window_start"], schedule["window_end"])

    load = load_by_day(schedule)
    for day, minutes in load.items():
        assert window[0] <= day <= window[1], f"{day} is outside the window {window}"
        assert days[day]["off_reason"] is None, f"{day} is a day off ({days[day]['off_reason']})"
        assert minutes <= days[day]["capacity_minutes"], f"{day}: {minutes} over capacity"
    for day, info in days.items():
        assert info["scheduled_minutes"] == load.get(day, 0), day
        assert info["scheduled_minutes"] <= info["capacity_minutes"], day

    for task_id, entry in placed.items():
        task = by_id[task_id]
        assert (entry["key_result_id"], entry["objective_id"]) == (
            task["key_result_id"],
            task["objective_id"],
        )
        dates = [a["date"] for a in entry["allocations"]]
        assert dates == sorted(dates) and len(dates) == len(set(dates)), task_id
        assert (entry["start_date"], entry["end_date"]) == (dates[0], dates[-1]), task_id
        assert sum(a["minutes"] for a in entry["allocations"]) == task["estimate_minutes"]
        for pred in task["depends_on"]:
            assert pred not in unscheduled, f"{task_id} is placed but {pred} is not"
            if pred in placed:
                assert placed[pred]["end_date"] < entry["start_date"], (pred, task_id)

    open_ids = {t["id"] for t in tasks if t["status"] != "done"}
    assert placed.keys() | unscheduled == open_ids
    assert not placed.keys() & unscheduled
