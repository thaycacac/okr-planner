"""Acceptance criterion 8: plan generation reports its progress while it runs.

The OpenAI time limit (a plan in at most 60 s) needs a real key and network, so it is measured
by ``evals/run_eval.py`` (column ``over_60s``), never in CI. Only that measurement is tested here.
"""

import time
from typing import Any

from app.planner_llm.providers.fake import FakeProvider
from evals import run_eval
from tests.acceptance.support import PlanLLM, create_objective, create_quarter, run_plan
from tests.api_support import ApiHarness

# The validate step is synchronous and reports no event of its own; the UI marks it done once
# the schedule stage starts.
STAGES = ["precheck", "clarify", "decompose", "dedup", "schedule"]


def _okr(api: ApiHarness) -> tuple[int, set[int]]:
    quarter_id = create_quarter(api)
    kr_ids: set[int] = set()
    for title, priority in (
        ("Ra mắt gói Team", "high"),
        ("Hoàn thiện trung tâm trợ giúp", "medium"),
    ):
        objective = create_objective(
            api, quarter_id, title, priority, [f"{title}: bước 1", f"{title}: bước 2"]
        )
        kr_ids |= {kr["id"] for kr in objective["key_results"]}
    return quarter_id, kr_ids


def test_progress_is_streamed_stage_by_stage_until_the_plan_is_ready(api: ApiHarness) -> None:
    api.provider.handler = PlanLLM()
    quarter_id, kr_ids = _okr(api)
    _, events = run_plan(api, quarter_id=quarter_id)

    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert all(e["run_status"] == "running" for e in events[:-1])
    assert events[-1] | {"type": "end", "run_status": "succeeded", "percent": 100} == events[-1]
    percents = [e["percent"] for e in events]
    assert percents == sorted(percents) and percents[0] < 100

    first_seen = list(dict.fromkeys(e["stage"] for e in events if e["stage"] is not None))
    assert first_seen == STAGES
    seen = {(e["stage"], e["status"]) for e in events}
    assert all((stage, "completed") in seen for stage in STAGES)
    completed = [e for e in events if e["stage"] == "decompose" and e["status"] == "completed"]
    assert {e["key_result_id"] for e in completed} == kr_ids
    assert sorted(e["completed"] for e in completed) == list(range(1, len(kr_ids) + 1))
    assert {e["total"] for e in completed} == {len(kr_ids)}


def test_progress_can_be_read_while_the_plan_is_still_running(api: ApiHarness) -> None:
    api.provider.handler = PlanLLM()
    api.provider.delay_seconds = 0.15
    quarter_id, _ = _okr(api)
    job_id = api.client.post("/plans", json={"quarter_id": quarter_id}).json()["job_id"]

    live: list[dict[str, Any]] = []
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        run = api.client.get(f"/plans/{job_id}").json()
        if run["status"] not in ("queued", "running"):
            break
        if run["progress"] is not None:
            live.append(run["progress"])
        time.sleep(0.02)

    assert run["status"] == "succeeded"
    stages = list(dict.fromkeys(p["stage"] for p in live))
    assert {"clarify", "decompose", "dedup"} <= set(stages), stages
    percents = [p["percent"] for p in live]
    assert percents == sorted(percents) and percents[-1] < 100
    assert all(p["run_status"] == "running" for p in live)


async def test_eval_flags_openai_plans_slower_than_sixty_seconds() -> None:
    assert run_eval.OPENAI_TIME_LIMIT_MS == 60_000
    (sample,) = run_eval.load_samples(["01"])
    records = []
    for duration_ms in (59_999, 60_000, 60_001):
        provider = FakeProvider(PlanLLM(), name="openai")
        record = await run_eval.run_one(sample, provider, max_retries=0)
        assert record["provider"] == "openai"
        record["sample_id"] = f"{sample.sample_id}@{duration_ms}"
        record["timing"]["duration_ms"] = duration_ms
        records.append(record)

    summary = run_eval.summarize_model(records, {})
    assert summary["over_60s"] == [f"{sample.sample_id}@60001"]
    assert "over_60s" not in run_eval.summarize_model(
        [r | {"provider": "local"} for r in records], {}
    )
