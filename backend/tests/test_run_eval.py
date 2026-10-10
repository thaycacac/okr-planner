import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.errors import InvalidJSONError, ProviderTimeoutError
from app.planner_llm.providers.fake import FakeProvider, FakeReply
from app.planner_llm.schemas import KeyResultCheck, KeyResultNeedsOutput
from evals import run_eval


class Handler:
    """Clear OKRs pass clarify; each KR gets two tasks; the first decompose call is not JSON."""

    def __init__(self, *, fail_first_decompose: bool = False) -> None:
        self.fail_first_decompose = fail_first_decompose

    def __call__(self, prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if schema is KeyResultCheck:
            return {"end_result": "done", "concrete": True}
        if schema is KeyResultNeedsOutput:
            return {"needs": []}
        if prompt.step == "dedup":
            return {"merges": [], "cross_dependencies": []}
        if self.fail_first_decompose:
            self.fail_first_decompose = False
            return InvalidJSONError("unterminated string")
        kr = prompt.kr_id
        return {
            "tasks": [
                _task("t1", kr, "Thiết kế bảng đo lường", []),
                _task("t2", kr, "Triển khai và kiểm thử", ["t1"]),
            ]
        }


def _task(local_id: str, kr: str | None, title: str, deps: list[str]) -> dict[str, Any]:
    return {
        "local_id": local_id,
        "title": title,
        "description": "Mô tả công việc",
        "estimate_hours": 4,
        "done_criteria": "Tài liệu được duyệt",
        "depends_on": deps,
        "kr_id": kr,
    }


def _sample(prefix: str) -> run_eval.Sample:
    (sample,) = run_eval.load_samples([prefix])
    return sample


def test_hours_per_day_is_read_from_context() -> None:
    assert _sample("01").hours_per_day == 4
    assert _sample("02").hours_per_day == 2
    assert _sample("03").usable_hours == 117
    assert _sample("08").usable_hours == 234
    assert _sample("03").budget.usable_hours == _sample("03").usable_hours


def test_working_days_come_from_the_app_calendar() -> None:
    # Q4/2026 has 66 weekdays; Tuesday 24 November is a public holiday in the VN data.
    assert run_eval.quarter_working_days(2026, 4) == 65
    assert all(s.working_days == 65 for s in run_eval.load_samples())


async def test_clear_sample_records_plan_metrics_and_retry() -> None:
    sample = _sample("01")
    provider = FakeProvider(Handler(fail_first_decompose=True), model="fake")
    record = await run_eval.run_one(sample, provider, max_retries=2)

    assert record["outcome"] == "ok"
    assert record["temperature"] == 0
    assert record["time_budget"] == {"working_days": 65, "total_hours": 260.0}
    decompose = next(c for c in provider.calls if c.step == "decompose")
    assert "65 working days left in the quarter at about 4 hours per day" in decompose.system
    assert len(record["tasks"]) == 2 * len(sample.kr_ids)
    assert record["json"]["invalid_json_attempts"] == 1
    assert record["json"]["retries"] == 1
    assert record["json"]["valid_after_retry"] == record["json"]["llm_calls"]
    assert set(record["timing"]["stage_duration_ms"]) >= {"precheck", "clarify", "decompose"}
    checks = record["auto_checks"]
    assert checks["false_clarification"] is False
    assert checks["c1a_all_krs_covered"] is True
    assert checks["c3a_estimates_in_range"] is True
    assert checks["total_hours"] == 8 * len(sample.kr_ids)
    assert checks["tasks_wrong_language"] == []


async def test_vague_sample_with_metric_gaps_asks_back() -> None:
    record = await run_eval.run_one(_sample("10"), FakeProvider(Handler()), max_retries=0)

    assert record["outcome"] == "needs_clarification"
    assert record["tasks"] == []
    checks = record["auto_checks"]
    assert checks["q1_status_and_no_tasks"] is True
    assert checks["question_count_1_to_5"] is True
    assert checks["questions_precheck"] >= 1


async def test_pipeline_failure_is_recorded_as_error() -> None:
    def broken(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        return InvalidJSONError("not json")

    record = await run_eval.run_one(_sample("01"), FakeProvider(broken), max_retries=1)

    assert record["outcome"] == "error"
    assert record["failure"]["code"] == "invalid_llm_output"
    assert record["json"]["valid_after_retry"] == record["json"]["llm_calls"] - 1


async def test_timeout_counts_as_invalid_output() -> None:
    def hangs(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if prompt.step == "dedup":
            return ProviderTimeoutError("local LLM timed out after 600s")
        return Handler()(prompt, schema)

    record = await run_eval.run_one(_sample("01"), FakeProvider(hangs), max_retries=2)

    assert record["failure"]["code"] == "provider_unavailable"
    assert record["json"]["failed_calls"] == 1
    assert record["json"]["timeout_attempts"] == 1
    assert record["json"]["schema_or_rule_rejections"] == 0
    assert record["json"]["valid_after_retry"] == record["json"]["llm_calls"] - 1


async def test_grading_pack_and_summary(tmp_path: Path) -> None:
    results = tmp_path / "results"
    model_dir = results / run_eval.model_slug("local", "fake:1b")
    model_dir.mkdir(parents=True)
    for prefix in ("01", "10"):
        record = await run_eval.run_one(_sample(prefix), FakeProvider(Handler()), max_retries=0)
        (model_dir / f"{record['sample_id']}.json").write_text(json.dumps(record), "utf-8")

    pack = tmp_path / "pack"
    run_eval.grading_pack(results, pack, seed=1)
    key = json.loads((pack / "key.json").read_text())
    (code,) = key
    assert key[code]["provider"] == "local"
    plan = (pack / f"01_saas_onboarding_vi__{code}.md").read_text()
    assert "fake" not in plan
    assert "| O1-KR1.t1 |" in plan
    run_eval.grading_pack(results, pack, seed=1)
    assert json.loads((pack / "key.json").read_text()) == key

    blinded = pack / f"scores_A_{code}.csv"
    blinded.write_text(
        f"sample_id,provider,model,grader,pass,notes\n01_saas_onboarding_vi,,{code},A,1,\n",
        "utf-8",
    )
    merged = tmp_path / "merged.csv"
    run_eval.merge_scores(pack, merged)
    (row,) = csv.DictReader(merged.open(encoding="utf-8"))
    assert (row["provider"], row["model"], row["grader"]) == ("local", key[code]["model"], "A")

    scores = tmp_path / "scores.csv"
    model = "fake-model:decompose"
    with scores.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sample_id", "provider", "model", "grader", "pass", "Q1", "C1", "notes"],
        )
        writer.writeheader()
        for grader, c1 in (("A", "1"), ("B", "0"), ("agreed", "1")):
            writer.writerow(
                {
                    "sample_id": "01_saas_onboarding_vi",
                    "provider": "local",
                    "model": model,
                    "grader": grader,
                    "pass": c1,
                    "C1": c1,
                    "Q1": "",
                    "notes": "",
                }
            )
            writer.writerow(
                {
                    "sample_id": "10_customer_support_missing_baseline_en",
                    "provider": "local",
                    "model": model,
                    "grader": grader,
                    "pass": "1",
                    "Q1": "1",
                    "C1": "",
                    "notes": "",
                }
            )

    summary = run_eval.summarize(results, scores)
    (only,) = summary["models"]
    assert only["pass_rate"] == 1.0
    assert only["clarify_correct"] == 1.0
    assert only["json_valid_after_retry"] == 1.0
    assert only["pass_rate_by_language"] == {"vi": 1.0, "en": 1.0}
    assert summary["grader_agreement"]["cell_agreement"] == 0.5
    assert (results / "summary.json").exists()
