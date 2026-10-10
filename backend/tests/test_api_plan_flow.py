"""End-to-end plan flow over HTTP with FakeProvider: quarter → OKR → plan → questions →
answers → schedule, and every task traces back to a key result."""

from datetime import date
from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.errors import ProviderConnectionError
from app.planner_llm.providers.fake import FakeReply
from tests.api_support import ApiHarness

VAGUE_KR = "Cải thiện hiệu suất làm việc"


def _create_okr(api: ApiHarness) -> dict[str, Any]:
    quarter = api.client.post("/quarters", json={"year": 2026, "number": 4}).json()
    growth = api.client.post(
        f"/quarters/{quarter['id']}/objectives",
        json={
            "title": "Phát triển kỹ năng chuyên môn trong quý",
            "priority": "high",
            "key_results": [
                {"text": VAGUE_KR, "kind": "numeric"},
                {"text": "Hoàn thành khóa học AWS Solutions Architect", "kind": "binary"},
            ],
        },
    )
    assert growth.status_code == 201
    health = api.client.post(
        f"/quarters/{quarter['id']}/objectives",
        json={
            "title": "Duy trì sức khỏe để làm việc bền bỉ",
            "priority": "low",
            "key_results": [{"text": "Chạy bộ 3 buổi mỗi tuần suốt quý", "kind": "binary"}],
        },
    )
    assert health.status_code == 201
    return {"quarter": quarter, "objectives": [growth.json(), health.json()]}


def _run(api: ApiHarness, path: str, body: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    response = api.client.post(path, json=body)
    assert response.status_code == 202, response.text
    job_id: str = response.json()["job_id"]
    return job_id, api.events(job_id)


def test_vague_okr_is_clarified_then_planned_and_scheduled(api: ApiHarness) -> None:
    okr = _create_okr(api)
    quarter_id = okr["quarter"]["id"]
    kr_ids = {kr["id"] for o in okr["objectives"] for kr in o["key_results"]}
    vague_kr_id = okr["objectives"][0]["key_results"][0]["id"]

    job_id, events = _run(api, "/plans", {"quarter_id": quarter_id})
    assert events[-1]["type"] == "end"
    assert events[-1]["run_status"] == "needs_clarification"
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert ("clarify", "completed") in {(e["stage"], e["status"]) for e in events}

    first = api.client.get(f"/plans/{job_id}").json()
    assert first["status"] == "needs_clarification"
    assert first["provider"] == "local"
    assert first["models"]["clarify"] == "fake-model:clarify"
    assert first["task_count"] == 0
    sources = {q["source"]: q for q in first["questions"]}
    assert sources["precheck"]["key_result_id"] == vague_kr_id
    assert sources["llm"]["key_result_id"] is None
    assert api.client.get(f"/quarters/{quarter_id}/schedule").status_code == 404

    answers = [
        {
            "question_id": q["id"],
            "answer": "Hiện 20 ticket/tuần, mục tiêu 30 ticket/tuần; 4 giờ/ngày",
        }
        for q in first["questions"]
    ]
    second_id, events = _run(api, f"/plans/{job_id}/answers", {"answers": answers})
    assert second_id != job_id
    assert events[-1] == {**events[-1], "type": "end", "run_status": "succeeded", "percent": 100}
    percents = [e["percent"] for e in events]
    assert percents == sorted(percents)
    decomposed = {
        e["key_result_id"]
        for e in events
        if e["stage"] == "decompose" and e["status"] == "completed"
    }
    assert decomposed == kr_ids
    assert ("schedule", "completed") in {(e["stage"], e["status"]) for e in events}

    second = api.client.get(f"/plans/{second_id}").json()
    assert second["status"] == "succeeded"
    assert second["parent_id"] == job_id
    assert second["round"] == 2
    assert second["task_count"] == 2 * len(kr_ids)
    assert second["schedule_run_id"] is not None
    assert set(second["models"]) == {"clarify", "decompose", "dedup"}
    assert {c["question_id"] for c in second["clarifications"]} == {
        a["question_id"] for a in answers
    }
    assert second["error"] is None

    detail = api.client.get(f"/quarters/{quarter_id}").json()
    assert detail["task_count"] == second["task_count"]
    assert detail["latest_plan_run_id"] == second_id
    tasks = {
        t["id"]: t for o in detail["objectives"] for kr in o["key_results"] for t in kr["tasks"]
    }
    for objective in detail["objectives"]:
        for kr in objective["key_results"]:
            assert kr["tasks"], f"key result {kr['id']} has no task"
            for task in kr["tasks"]:
                assert task["key_result_id"] == kr["id"]
                assert task["objective_id"] == objective["id"]
                assert task["plan_run_id"] == second_id
                assert set(task["depends_on"]) <= tasks.keys()

    schedule = api.client.get(f"/quarters/{quarter_id}/schedule").json()
    assert schedule["plan_run_id"] == second_id
    assert schedule["window_start"] == "2026-10-01"
    assert schedule["window_end"] == "2026-12-31"
    assert schedule["feasibility"]["status"] == "green"
    assert schedule["unscheduled"] == []
    assert {s["task_id"] for s in schedule["tasks"]} == tasks.keys()
    for placed in schedule["tasks"]:
        task = tasks[placed["task_id"]]
        assert placed["key_result_id"] == task["key_result_id"] in kr_ids
        assert placed["objective_id"] == task["objective_id"]
        assert sum(a["minutes"] for a in placed["allocations"]) == task["estimate_minutes"]
        for allocation in placed["allocations"]:
            assert date.fromisoformat(allocation["date"]).weekday() < 5

    days = {d["date"]: d for d in schedule["days"]}
    assert len(days) == 92
    assert days["2026-10-03"]["off_reason"] == "weekend"
    for day in days.values():
        assert day["scheduled_minutes"] <= day["capacity_minutes"]

    by_objective: dict[int, list[str]] = {}
    for placed in schedule["tasks"]:
        by_objective.setdefault(placed["objective_id"], []).append(placed["start_date"])
    high, low = (o["id"] for o in okr["objectives"])
    assert min(by_objective[high]) < min(by_objective[low])


def test_decompose_is_told_the_time_left_in_the_quarter(api: ApiHarness) -> None:
    quarter_id = _create_okr(api)["quarter"]["id"]
    leave = api.client.post("/calendar/leave-days", json={"start_date": "2026-10-02"})
    assert leave.status_code == 201, leave.text

    _, events = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": True})

    assert events[-1]["run_status"] == "succeeded"
    prompts = [c.system for c in api.provider.calls if c.step == "decompose"]
    assert len(prompts) == 3
    # Q4/2026 has 65 working days (24/11 is a holiday); the leave day takes one more.
    for system in prompts:
        assert "64 working days left in the quarter at about 4 hours per day" in system
        assert "256 hours in total, 230.4 hours usable" in system
        assert "All 3 key results of the plan share this budget" in system


def test_events_replay_after_last_event_id(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    quarter_id = _create_okr(api)["quarter"]["id"]
    job_id, events = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": True})
    assert events[-1]["run_status"] == "succeeded"

    replay = api.events(job_id, last_event_id=events[-3]["seq"])
    assert replay == events[-2:]


def test_provider_failure_is_reported_with_suggestions(api: ApiHarness) -> None:
    api.llm.overrides["clarify"] = ProviderConnectionError("cannot reach local LLM")
    quarter_id = _create_okr(api)["quarter"]["id"]

    job_id, events = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": False})
    assert events[-1]["run_status"] == "failed"

    run = api.client.get(f"/plans/{job_id}").json()
    assert run["status"] == "failed"
    assert run["error"]["code"] == "provider_unavailable"
    assert run["error"]["step"] == "clarify"
    assert "switch_provider" in run["error"]["suggestions"]
    assert run["provider"] == "local"
    assert run["task_count"] == 0


def _fail_decompose_of(api: ApiHarness, kr_id: int) -> None:
    scripted = api.llm

    def handler(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if prompt.step == "decompose" and prompt.kr_id == f"kr{kr_id}":
            return ProviderConnectionError("local LLM timed out")
        return scripted(prompt, schema)

    api.provider.handler = handler


def _decomposed_krs(api: ApiHarness, since: int = 0) -> list[str | None]:
    return [c.kr_id for c in api.provider.calls[since:] if c.step == "decompose"]


def test_failed_decompose_resumes_with_the_finished_key_results(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    api.provider.max_concurrency = 1
    okr = _create_okr(api)
    quarter_id = okr["quarter"]["id"]
    kr_ids = [kr["id"] for o in okr["objectives"] for kr in o["key_results"]]
    failing = kr_ids[-1]
    _fail_decompose_of(api, failing)

    failed_id, events = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": True})
    assert events[-1]["run_status"] == "failed"
    failed = api.client.get(f"/plans/{failed_id}").json()
    assert (failed["error"]["step"], failed["error"]["key_result_id"]) == ("decompose", failing)
    assert failed["resumable"] is True
    assert _decomposed_krs(api) == [f"kr{i}" for i in kr_ids]

    api.provider.handler = api.llm
    before = len(api.provider.calls)
    resumed_id, events = _run(api, f"/plans/{failed_id}/resume", {})
    assert resumed_id != failed_id
    assert events[-1]["run_status"] == "succeeded"
    assert _decomposed_krs(api, before) == [f"kr{failing}"]
    decomposed = {
        e["key_result_id"]
        for e in events
        if e["stage"] == "decompose" and e["status"] == "completed"
    }
    assert decomposed == set(kr_ids)

    resumed = api.client.get(f"/plans/{resumed_id}").json()
    assert resumed["parent_id"] == failed_id
    assert resumed["round"] == failed["round"]
    assert resumed["task_count"] == 2 * len(kr_ids)
    assert resumed["resumable"] is False
    tasks = api.client.get(f"/quarters/{quarter_id}/tasks").json()
    assert {t["key_result_id"] for t in tasks} == set(kr_ids)
    assert {t["plan_run_id"] for t in tasks} == {resumed_id}
    assert api.client.get(f"/plans/{failed_id}").json()["resumable"] is False

    again = api.client.post(f"/plans/{failed_id}/resume")
    assert again.status_code == 409
    assert again.json()["detail"]["code"] == "plan_not_resumable"


def test_failed_resume_keeps_every_finished_key_result(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    api.provider.max_concurrency = 1
    okr = _create_okr(api)
    kr_ids = [kr["id"] for o in okr["objectives"] for kr in o["key_results"]]
    _fail_decompose_of(api, kr_ids[1])
    body = {"quarter_id": okr["quarter"]["id"], "skip_clarification": True}
    first_id, _ = _run(api, "/plans", body)

    _fail_decompose_of(api, kr_ids[2])
    second_id, events = _run(api, f"/plans/{first_id}/resume", {})
    assert events[-1]["run_status"] == "failed"

    api.provider.handler = api.llm
    before = len(api.provider.calls)
    _, events = _run(api, f"/plans/{second_id}/resume", {})
    assert events[-1]["run_status"] == "succeeded"
    assert _decomposed_krs(api, before) == [f"kr{kr_ids[2]}"]


def test_failed_dedup_resumes_without_decomposing_again(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    api.llm.overrides["dedup"] = ProviderConnectionError("local LLM timed out")
    quarter_id = _create_okr(api)["quarter"]["id"]
    failed_id, _ = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": True})
    assert api.client.get(f"/plans/{failed_id}").json()["error"]["step"] == "dedup"

    del api.llm.overrides["dedup"]
    before = len(api.provider.calls)
    _, events = _run(api, f"/plans/{failed_id}/resume", {})
    assert events[-1]["run_status"] == "succeeded"
    assert {c.step for c in api.provider.calls[before:]} == {"dedup"}


def test_resume_is_refused_once_the_okr_changed(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    okr = _create_okr(api)
    kr_id = okr["objectives"][1]["key_results"][0]["id"]
    _fail_decompose_of(api, kr_id)
    body = {"quarter_id": okr["quarter"]["id"], "skip_clarification": True}
    failed_id, _ = _run(api, "/plans", body)

    edited = api.client.patch(f"/key-results/{kr_id}", json={"text": "Chạy bộ 4 buổi mỗi tuần"})
    assert edited.status_code == 200
    assert api.client.get(f"/plans/{failed_id}").json()["resumable"] is False
    response = api.client.post(f"/plans/{failed_id}/resume")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "okr_changed"


def test_only_decompose_and_dedup_failures_can_resume(api: ApiHarness) -> None:
    api.llm.overrides["clarify"] = ProviderConnectionError("cannot reach local LLM")
    quarter_id = _create_okr(api)["quarter"]["id"]
    failed_id, _ = _run(api, "/plans", {"quarter_id": quarter_id})
    assert api.client.get(f"/plans/{failed_id}").json()["resumable"] is False
    response = api.client.post(f"/plans/{failed_id}/resume")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "plan_not_resumable"

    del api.llm.overrides["clarify"]
    api.llm.clarify_question = None
    done_id, _ = _run(api, "/plans", {"quarter_id": quarter_id, "skip_clarification": True})
    assert api.client.post(f"/plans/{done_id}/resume").status_code == 409
    assert api.client.post("/plans/unknown/resume").status_code == 404


def test_invalid_okr_returns_precheck_issues(api: ApiHarness) -> None:
    quarter = api.client.post("/quarters", json={"year": 2026, "number": 4}).json()
    api.client.post(
        f"/quarters/{quarter['id']}/objectives", json={"title": "Objective without key results"}
    )

    job_id, events = _run(api, "/plans", {"quarter_id": quarter["id"]})
    assert events[-1]["run_status"] == "invalid_input"
    run = api.client.get(f"/plans/{job_id}").json()
    assert [i["code"] for i in run["issues"]] == ["no_key_results"]
    assert api.provider.calls == []


def test_regenerating_keeps_done_tasks_and_replaces_the_rest(api: ApiHarness) -> None:
    api.llm.clarify_question = None
    quarter_id = _create_okr(api)["quarter"]["id"]
    body = {"quarter_id": quarter_id, "skip_clarification": True}
    first_id, _ = _run(api, "/plans", body)
    second_id, events = _run(api, "/plans", body)
    assert events[-1]["run_status"] == "succeeded"

    tasks = api.client.get(f"/quarters/{quarter_id}/tasks").json()
    assert {t["plan_run_id"] for t in tasks} == {second_id}
    assert first_id != second_id


def test_answers_are_validated(api: ApiHarness) -> None:
    quarter_id = _create_okr(api)["quarter"]["id"]
    job_id, _ = _run(api, "/plans", {"quarter_id": quarter_id})

    unknown = api.client.post(
        f"/plans/{job_id}/answers", json={"answers": [{"question_id": "q99", "answer": "x"}]}
    )
    assert unknown.status_code == 422
    assert unknown.json()["detail"]["code"] == "unknown_question"

    missing = api.client.post("/plans/nope/answers", json={"answers": []})
    assert missing.status_code == 404

    api.client.post(f"/plans/{job_id}/answers", json={"answers": [], "generate_anyway": True})
    again = api.client.post(f"/plans/{job_id}/answers", json={"answers": []})
    assert again.status_code == 409


def test_running_plan_blocks_a_second_one_and_can_be_cancelled(api: ApiHarness) -> None:
    api.provider.delay_seconds = 30
    quarter_id = _create_okr(api)["quarter"]["id"]
    job_id = api.client.post("/plans", json={"quarter_id": quarter_id}).json()["job_id"]

    busy = api.client.post("/plans", json={"quarter_id": quarter_id})
    assert busy.status_code == 409
    assert busy.json()["detail"]["code"] == "plan_in_progress"

    cancelled = api.client.post(f"/plans/{job_id}/cancel")
    assert cancelled.status_code == 202
    assert cancelled.json()["status"] == "cancelled"
    assert api.events(job_id)[-1]["run_status"] == "cancelled"
    assert api.client.post(f"/plans/{job_id}/cancel").status_code == 409


def test_event_stream_opts_out_of_proxy_buffering(api: ApiHarness) -> None:
    quarter_id = _create_okr(api)["quarter"]["id"]
    job_id = api.client.post("/plans", json={"quarter_id": quarter_id}).json()["job_id"]
    with api.client.stream(
        "GET", f"/plans/{job_id}/events", headers={"Accept-Encoding": "gzip, deflate, br"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache, no-transform"
        assert response.headers["x-accel-buffering"] == "no"
        assert "content-encoding" not in response.headers
        assert "data: " in "".join(response.iter_text())


def test_plan_for_missing_quarter_is_404(api: ApiHarness) -> None:
    response = api.client.post("/plans", json={"quarter_id": 999})
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "not_found", "message": "quarter 999 not found"}}
    assert api.client.get("/plans/unknown").status_code == 404
    assert api.client.get("/plans/unknown/events").status_code == 404
