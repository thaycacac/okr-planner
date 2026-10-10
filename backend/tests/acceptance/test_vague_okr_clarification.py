"""Acceptance criterion 5: a vague OKR is asked back and no plan (tasks, schedule) is generated
until the user answers or explicitly chooses to generate anyway."""

from tests.acceptance.support import PlanLLM, create_objective, create_quarter, run_plan, tasks_of
from tests.api_support import ApiHarness

VAGUE_KR = "Tăng doanh thu từ khách hàng doanh nghiệp"


def _assert_no_plan(api: ApiHarness, quarter_id: int) -> None:
    assert tasks_of(api, quarter_id) == []
    assert api.client.get(f"/quarters/{quarter_id}/schedule").status_code == 404
    assert [c for c in api.provider.calls if c.step in ("decompose", "dedup")] == []


def test_key_result_without_baseline_or_target_is_asked_back_without_a_plan(
    api: ApiHarness,
) -> None:
    api.provider.handler = PlanLLM()
    quarter_id = create_quarter(api)
    objective = create_objective(
        api, quarter_id, "Mở rộng thị trường doanh nghiệp", "high", [VAGUE_KR]
    )
    vague_id = objective["key_results"][0]["id"]

    job_id, events = run_plan(api, quarter_id=quarter_id)
    assert events[-1]["run_status"] == "needs_clarification"
    run = api.client.get(f"/plans/{job_id}").json()
    assert run["status"] == "needs_clarification" and run["task_count"] == 0
    [question] = run["questions"]
    assert (question["source"], question["key_result_id"]) == ("precheck", vague_id)
    assert "baseline" in question["question"]
    _assert_no_plan(api, quarter_id)


def test_okr_the_llm_finds_unclear_is_asked_back_without_a_plan(api: ApiHarness) -> None:
    quarter_id = create_quarter(api)
    create_objective(
        api, quarter_id, "Phát triển bản thân", "medium", ["Làm việc hiệu quả hơn mỗi ngày"]
    )

    job_id, events = run_plan(api, quarter_id=quarter_id)
    assert events[-1]["run_status"] == "needs_clarification"
    run = api.client.get(f"/plans/{job_id}").json()
    assert [q["source"] for q in run["questions"]] == ["llm"]
    assert run["questions"][0]["question"] == api.llm.clarify_question
    _assert_no_plan(api, quarter_id)


def test_answering_the_questions_unlocks_the_plan(api: ApiHarness) -> None:
    quarter_id = create_quarter(api)
    objective = create_objective(
        api,
        quarter_id,
        "Mở rộng thị trường doanh nghiệp",
        "high",
        [VAGUE_KR, "Làm việc hiệu quả hơn mỗi ngày"],
    )
    first_id, _ = run_plan(api, quarter_id=quarter_id)
    questions = api.client.get(f"/plans/{first_id}").json()["questions"]
    assert {q["source"] for q in questions} == {"precheck", "llm"}

    answers = [
        {"question_id": q["id"], "answer": "Hiện 1 tỷ/quý, mục tiêu 1,5 tỷ/quý; 4 giờ/ngày"}
        for q in questions
    ]
    second_id, events = run_plan(api, f"/plans/{first_id}/answers", answers=answers)
    assert events[-1]["run_status"] == "succeeded"
    tasks = tasks_of(api, quarter_id)
    assert {t["key_result_id"] for t in tasks} == {kr["id"] for kr in objective["key_results"]}
    assert api.client.get(f"/quarters/{quarter_id}/schedule").json()["plan_run_id"] == second_id


def test_okr_without_key_results_is_rejected_before_any_llm_call(api: ApiHarness) -> None:
    quarter_id = create_quarter(api)
    create_objective(api, quarter_id, "Mục tiêu chưa có kết quả then chốt", "high", [])

    job_id, events = run_plan(api, quarter_id=quarter_id)
    assert events[-1]["run_status"] == "invalid_input"
    run = api.client.get(f"/plans/{job_id}").json()
    assert [i["code"] for i in run["issues"]] == ["no_key_results"]
    assert api.provider.calls == []
    _assert_no_plan(api, quarter_id)
