"""Run the planner pipeline on the eval OKR samples and summarise the results.

Run from ``backend/``::

    python -m evals.run_eval run --provider local --model qwen3:8b
    python -m evals.run_eval run --provider openai --model gpt-4o-mini
    python -m evals.run_eval grading-pack
    python -m evals.run_eval summarize

``run`` writes one JSON file per sample to ``results/<provider>__<model>/`` with the pipeline
outcome, the plan, per-step timings, retries, rejected attempts and the rubric parts that
can be checked mechanically. The rubric itself (``RUBRIC.md``) is scored by graders;
``grading-pack`` writes blinded plans for them and ``summarize`` combines the machine
metrics with the agreed scores in ``results/scores.csv``.
"""

import argparse
import asyncio
import csv
import functools
import hashlib
import json
import os
import re
import statistics
import sys
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.calendar import load_holidays, working_days
from app.domain.calendar_config import CalendarConfig
from app.domain.quarter import Quarter
from app.planner_llm.pipeline import run_pipeline
from app.planner_llm.providers.base import LLMProvider
from app.planner_llm.providers.local import LocalProvider
from app.planner_llm.providers.openai_provider import OpenAIProvider
from app.planner_llm.schemas import OkrInput, PipelineError, PipelineResult, TimeBudget
from app.planner_llm.validation import MAX_QUESTIONS, MAX_TASK_HOURS, MIN_TASK_HOURS

EVALS_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = EVALS_DIR / "okr_samples"
RESULTS_DIR = EVALS_DIR / "results"
SCORES_FILE = RESULTS_DIR / "scores.csv"

DEFAULT_HOURS_PER_DAY = 4.0
USABLE_SHARE = 0.9
OPENAI_TIME_LIMIT_MS = 60_000
JSON_VALID_TARGET = 0.98
PASS_TARGET = 0.8

_HOURS_PER_DAY = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:giờ|hours?)\s*(?:mỗi ngày|per workday|per day|a day)",
    re.IGNORECASE,
)
_VI_DIACRITICS = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
    re.IGNORECASE,
)
_DIGIT = re.compile(r"\d")
_INVALID_JSON_MARK = "not valid JSON"
_TIMEOUT_MARK = "timed out"
_SCORE_COLUMNS = ("Q1", "Q2", "Q3", "C1", "C2", "C3", "C4", "C5", "C6")


@functools.cache
def quarter_working_days(year: int, number: int) -> int:
    """Working days of a whole quarter with the app's default calendar and VN holiday data."""
    quarter = Quarter(year=year, number=number)
    holidays = load_holidays([year])
    config = CalendarConfig(makeup_days=holidays.makeup_dates)
    return len(working_days(quarter.start, quarter.end, config, holidays.holiday_dates))


@dataclass(frozen=True)
class Sample:
    sample_id: str
    raw: dict[str, Any]

    @property
    def okr(self) -> OkrInput:
        return OkrInput.model_validate(self.raw["input"])

    @property
    def language(self) -> str:
        return str(self.raw["input"]["language"])

    @property
    def expected(self) -> dict[str, Any]:
        expected: dict[str, Any] = self.raw["expected"]
        return expected

    @property
    def expects_clarification(self) -> bool:
        return bool(self.expected["clarify_status"] == "needs_clarification")

    @property
    def kr_ids(self) -> list[str]:
        return [kr["id"] for o in self.raw["input"]["objectives"] for kr in o["key_results"]]

    @property
    def hours_per_day(self) -> float:
        match = _HOURS_PER_DAY.search(self.raw["input"].get("context") or "")
        return float(match.group(1).replace(",", ".")) if match else DEFAULT_HOURS_PER_DAY

    @property
    def working_days(self) -> int:
        quarter = self.raw["quarter"]
        return quarter_working_days(int(quarter["year"]), int(quarter["number"]))

    @property
    def usable_hours(self) -> float:
        return round(self.working_days * self.hours_per_day * USABLE_SHARE, 1)

    @property
    def budget(self) -> TimeBudget:
        """What the app passes from the calendar: the whole quarter at the sample's daily hours."""
        return TimeBudget(
            working_days=self.working_days,
            total_hours=self.working_days * self.hours_per_day,
        )


def load_samples(only: Sequence[str] = ()) -> list[Sample]:
    samples = []
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        if only and not any(path.stem.startswith(prefix) for prefix in only):
            continue
        samples.append(Sample(path.stem, json.loads(path.read_text(encoding="utf-8"))))
    return samples


def model_slug(provider: str, model: str) -> str:
    return f"{provider}__{re.sub(r'[^A-Za-z0-9._-]+', '-', model)}"


def build_provider(args: argparse.Namespace) -> LLMProvider:
    if args.provider == "local":
        return LocalProvider(
            base_url=args.base_url,
            model=args.model,
            max_concurrency=args.concurrency or 1,
            timeout_seconds=args.timeout or 600.0,
        )
    return OpenAIProvider(
        api_key=os.environ.get("OPENAI_API_KEY"),
        models={"clarify": args.model, "decompose": args.model, "dedup": args.model},
        max_concurrency=args.concurrency or 5,
        timeout_seconds=args.timeout or 60.0,
    )


# ---------------------------------------------------------------------------
# Machine metrics for one run
# ---------------------------------------------------------------------------


def _has_vi_marks(text: str) -> bool:
    return bool(_VI_DIACRITICS.search(text))


def _wrong_language(texts: Iterable[str], language: str) -> bool:
    joined = " ".join(texts)
    return _has_vi_marks(joined) != (language == "vi")


def json_metrics(steps: Sequence[dict[str, Any]], failure: dict[str, Any] | None) -> dict[str, Any]:
    llm_steps = [s for s in steps if s.get("model")]
    rejected = [e for s in llm_steps for e in s.get("errors", []) if e.startswith("attempt ")]
    invalid_json = [e for e in rejected if _INVALID_JSON_MARK in e]
    timeouts = [e for e in rejected if _TIMEOUT_MARK in e]
    # A timeout is counted too: runaway generation under a JSON grammar never yields a document.
    failed_calls = 1 if failure and failure.get("step") in {"clarify", "decompose", "dedup"} else 0
    return {
        "llm_calls": len(llm_steps),
        "first_attempt_valid": sum(1 for s in llm_steps if s.get("attempts") == 1),
        "valid_after_retry": len(llm_steps) - failed_calls,
        "failed_calls": failed_calls,
        "failure_code": failure.get("code") if failure else None,
        "retries": sum(int(s.get("retries", 0)) for s in llm_steps),
        "rejected_attempts": len(rejected),
        "invalid_json_attempts": len(invalid_json),
        "timeout_attempts": len(timeouts),
        "schema_or_rule_rejections": len(rejected) - len(invalid_json) - len(timeouts),
    }


def auto_checks(sample: Sample, outcome: str, result: dict[str, Any]) -> dict[str, Any]:
    """Rubric parts that need no judgement; graders still score every criterion."""
    tasks: list[dict[str, Any]] = result.get("tasks", [])
    questions: list[dict[str, Any]] = result.get("questions", [])
    checks: dict[str, Any] = {}
    if sample.expects_clarification:
        llm_questions = [q for q in questions if q.get("source") == "llm"]
        checks["q1_status_and_no_tasks"] = outcome == "needs_clarification" and not tasks
        checks["question_count_1_to_5"] = 1 <= len(questions) <= MAX_QUESTIONS
        checks["questions_precheck"] = len(questions) - len(llm_questions)
        checks["questions_llm"] = len(llm_questions)
        checks["llm_questions_with_digits"] = sum(
            1 for q in llm_questions if _DIGIT.search(q.get("question", ""))
        )
        checks["questions_wrong_language"] = sum(
            1 for q in questions if _wrong_language([q.get("question", "")], sample.language)
        )
        return checks

    checks["false_clarification"] = outcome == "needs_clarification"
    if outcome != "ok":
        return checks
    total = round(sum(float(t["estimate_hours"]) for t in tasks), 1)
    expected_total = sample.expected["total_hours_range"]
    ids = {t["local_id"] for t in tasks}
    covered = {t["kr_id"] for t in tasks}
    checks.update(
        {
            "task_count": len(tasks),
            "total_hours": total,
            "expected_total_hours": [expected_total["min"], expected_total["max"]],
            "usable_hours": sample.usable_hours,
            "c1a_all_krs_covered": all(kr in covered for kr in sample.kr_ids),
            "c3a_estimates_in_range": all(
                MIN_TASK_HOURS <= float(t["estimate_hours"]) <= MAX_TASK_HOURS for t in tasks
            ),
            "c3b_total_in_expected_range": expected_total["min"] <= total <= expected_total["max"],
            "c4a_dependencies_resolve": all(d in ids for t in tasks for d in t["depends_on"]),
            "c6a_within_usable_hours": total <= sample.usable_hours,
            "tasks_wrong_language": sorted(
                t["local_id"]
                for t in tasks
                if _wrong_language([t["title"], t["done_criteria"]], sample.language)
            ),
            "tasks_per_kr": {kr: sum(1 for t in tasks if t["kr_id"] == kr) for kr in sample.kr_ids},
            "hours_per_kr": {
                kr: round(sum(float(t["estimate_hours"]) for t in tasks if t["kr_id"] == kr), 1)
                for kr in sample.kr_ids
            },
        }
    )
    return checks


async def run_one(sample: Sample, provider: LLMProvider, max_retries: int) -> dict[str, Any]:
    started = time.perf_counter()
    failure: dict[str, Any] | None = None
    outcome: str
    try:
        result: PipelineResult = await run_pipeline(
            sample.okr, provider, max_retries=max_retries, budget=sample.budget
        )
        payload = result.model_dump(mode="json")
        outcome = result.status
    except PipelineError as exc:
        failure = exc.failure.model_dump(mode="json")
        payload = {"trace": exc.trace.model_dump(mode="json"), "tasks": [], "questions": []}
        outcome = "error"
    wall_ms = round((time.perf_counter() - started) * 1000)
    trace = payload.pop("trace")
    return {
        "sample_id": sample.sample_id,
        "language": sample.language,
        "expected_clarify_status": sample.expected["clarify_status"],
        "provider": provider.name,
        "model": provider.model_for("decompose"),
        "temperature": 0,
        "max_retries": max_retries,
        "time_budget": sample.budget.model_dump(),
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "outcome": outcome,
        "wall_ms": wall_ms,
        "failure": failure,
        "questions": payload.get("questions", []),
        "issues": payload.get("issues", []),
        "tasks": payload.get("tasks", []),
        "timing": {
            "duration_ms": trace["duration_ms"],
            "stage_duration_ms": trace["stage_duration_ms"],
        },
        "json": json_metrics(trace["steps"], failure),
        "auto_checks": auto_checks(sample, outcome, payload),
        "trace": trace,
    }


async def run_eval(args: argparse.Namespace) -> Path:
    provider = build_provider(args)
    out_dir = Path(args.out_dir) / model_slug(args.provider, args.model)
    out_dir.mkdir(parents=True, exist_ok=True)
    for sample in load_samples(args.samples):
        target = out_dir / f"{sample.sample_id}.json"
        if target.exists() and not args.force:
            print(f"skip {sample.sample_id} (exists)", flush=True)
            continue
        record = await run_one(sample, provider, args.max_retries)
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(
            f"{sample.sample_id}: {record['outcome']} tasks={len(record['tasks'])} "
            f"questions={len(record['questions'])} retries={record['json']['retries']} "
            f"time={record['timing']['duration_ms'] / 1000:.1f}s",
            flush=True,
        )
    return out_dir


# ---------------------------------------------------------------------------
# Blinded grading pack
# ---------------------------------------------------------------------------


def _plan_markdown(code: str, record: dict[str, Any]) -> str:
    lines = [f"# Plan {code} — sample {record['sample_id']}", ""]
    lines.append(f"- Pipeline status: `{record['outcome']}`")
    if record["failure"]:
        lines.append(f"- Failure: `{record['failure']['code']}` at `{record['failure']['step']}`")
    if record["questions"]:
        lines += ["", "## Questions", ""]
        lines += [
            f"{i}. [{q['source']}; kr={q['kr_id']}] {q['question']} — _{q['reason']}_"
            for i, q in enumerate(record["questions"], start=1)
        ]
    if record["tasks"]:
        total = sum(float(t["estimate_hours"]) for t in record["tasks"])
        lines += ["", f"## Tasks ({len(record['tasks'])} tasks, {total:g} h)", ""]
        lines.append("| id | kr | h | depends_on | title | done_criteria |")
        lines.append("|---|---|---|---|---|---|")
        for t in record["tasks"]:
            cells = [
                t["local_id"],
                t["kr_id"],
                f"{float(t['estimate_hours']):g}",
                ", ".join(t["depends_on"]) or "—",
                t["title"],
                t["done_criteria"],
            ]
            lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
        lines += ["", "### Descriptions", ""]
        lines += [f"- **{t['local_id']}**: {t['description']}" for t in record["tasks"]]
    return "\n".join(lines) + "\n"


def load_records(results_dir: Path) -> list[dict[str, Any]]:
    """Load run records; JSON metrics are recomputed from the trace so definitions stay current."""
    records = []
    for path in sorted(results_dir.glob("*__*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["json"] = json_metrics(record["trace"]["steps"], record["failure"])
        records.append(record)
    return records


def grading_pack(results_dir: Path, out_dir: Path, seed: int) -> None:
    """Codes are a salted hash so a model keeps its code when packs are built incrementally."""
    records = load_records(results_dir)
    models = sorted({(r["provider"], r["model"]) for r in records})
    by_model = {
        (p, m): "M" + hashlib.sha256(f"{seed}:{p}:{m}".encode()).hexdigest()[:4] for p, m in models
    }
    key = {code: {"provider": p, "model": m} for (p, m), code in sorted(by_model.items())}
    out_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        code = by_model[(record["provider"], record["model"])]
        name = f"{record['sample_id']}__{code}.md"
        (out_dir / name).write_text(_plan_markdown(code, record), "utf-8")
    (out_dir / "key.json").write_text(json.dumps(key, indent=2) + "\n", "utf-8")
    print(f"wrote {len(records)} plans for {len(models)} models to {out_dir}")


def merge_scores(grading_dir: Path, scores_path: Path) -> None:
    """Combine ``scores_<grader>_<code>.csv`` sheets, replacing codes with provider/model."""
    key: dict[str, dict[str, str]] = json.loads((grading_dir / "key.json").read_text("utf-8"))
    header = (EVALS_DIR / "scoresheet_template.csv").read_text("utf-8").splitlines()[0]
    fieldnames = header.split(",")
    rows: list[dict[str, str]] = []
    for sheet in sorted(grading_dir.glob("scores_*_*.csv")):
        with sheet.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                model = key[row["model"]]
                rows.append({**row, "provider": model["provider"], "model": model["model"]})
    rows.sort(key=lambda r: (r["provider"], r["model"], r["sample_id"], r["grader"]))
    with scores_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {scores_path}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 3) if denominator else None


def _load_scores(path: Path, grader: str) -> dict[tuple[str, str, str], dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("grader") == grader]
    return {(r["provider"], r["model"], r["sample_id"]): r for r in rows}


def agreement(path: Path, grader_a: str, grader_b: str) -> dict[str, Any]:
    a, b = _load_scores(path, grader_a), _load_scores(path, grader_b)
    cells = same = verdicts = same_verdict = 0
    for key in a.keys() & b.keys():
        for column in _SCORE_COLUMNS:
            x, y = a[key].get(column, ""), b[key].get(column, "")
            if x == "" and y == "":
                continue
            cells += 1
            same += x == y
        verdicts += 1
        same_verdict += a[key].get("pass") == b[key].get("pass")
    return {
        "rows": len(a.keys() & b.keys()),
        "cells": cells,
        "cell_agreement": _rate(same, cells),
        "disagreeing_cells": cells - same,
        "verdict_agreement": _rate(same_verdict, verdicts),
    }


def summarize_model(
    records: list[dict[str, Any]], scores: dict[Any, dict[str, str]]
) -> dict[str, Any]:
    provider, model = records[0]["provider"], records[0]["model"]
    clarify = [r for r in records if r["expected_clarify_status"] == "needs_clarification"]
    clear = [r for r in records if r["expected_clarify_status"] == "ok"]
    calls = sum(r["json"]["llm_calls"] for r in records)
    durations = [r["timing"]["duration_ms"] for r in records]
    stage_ms: dict[str, list[int]] = defaultdict(list)
    for r in records:
        for stage, ms in r["timing"]["stage_duration_ms"].items():
            stage_ms[stage].append(ms)
    summary: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "samples": len(records),
        "outcomes": {
            o: sum(1 for r in records if r["outcome"] == o)
            for o in ("ok", "needs_clarification", "invalid_input", "error")
        },
        "errors": [
            f"{r['sample_id']}: {r['failure']['code']}@{r['failure']['step']}"
            for r in records
            if r["failure"]
        ],
        "clarify_correct": _rate(
            sum(1 for r in clarify if r["auto_checks"].get("q1_status_and_no_tasks")), len(clarify)
        ),
        "no_false_clarification": _rate(
            sum(1 for r in clear if not r["auto_checks"].get("false_clarification")), len(clear)
        ),
        "llm_calls": calls,
        "json_first_attempt_valid": _rate(
            sum(r["json"]["first_attempt_valid"] for r in records), calls
        ),
        "json_valid_after_retry": _rate(
            sum(r["json"]["valid_after_retry"] for r in records), calls
        ),
        "retries": sum(r["json"]["retries"] for r in records),
        "invalid_json_attempts": sum(r["json"]["invalid_json_attempts"] for r in records),
        "schema_or_rule_rejections": sum(r["json"]["schema_or_rule_rejections"] for r in records),
        "duration_s": {
            "median": round(statistics.median(durations) / 1000, 1),
            "max": round(max(durations) / 1000, 1),
            "total": round(sum(durations) / 1000, 1),
        },
        "stage_mean_s": {s: round(statistics.mean(v) / 1000, 1) for s, v in stage_ms.items()},
    }
    if provider == "openai":
        summary["over_60s"] = [
            r["sample_id"] for r in records if r["timing"]["duration_ms"] > OPENAI_TIME_LIMIT_MS
        ]
    auto = [r["auto_checks"] for r in clear if r["outcome"] == "ok"]
    for check in (
        "c1a_all_krs_covered",
        "c3a_estimates_in_range",
        "c3b_total_in_expected_range",
        "c4a_dependencies_resolve",
        "c6a_within_usable_hours",
    ):
        summary[f"auto_{check}"] = _rate(sum(1 for a in auto if a.get(check)), len(auto))

    rows = [scores[k] for k in scores if k[0] == provider and k[1] == model]
    if rows:
        graded = [r for r in rows if "excluded" not in r.get("notes", "")]
        summary["graded"] = len(graded)
        summary["pass_rate"] = _rate(sum(1 for r in graded if r["pass"] == "1"), len(graded))
        summary["criteria"] = {
            c: _rate(
                sum(1 for r in graded if r.get(c) == "1"),
                sum(1 for r in graded if r.get(c, "") != ""),
            )
            for c in _SCORE_COLUMNS
        }
        languages = {r["sample_id"]: r["language"] for r in records}
        summary["pass_rate_by_language"] = {
            lang: _rate(
                sum(
                    1 for r in graded if languages.get(r["sample_id"]) == lang and r["pass"] == "1"
                ),
                sum(1 for r in graded if languages.get(r["sample_id"]) == lang),
            )
            for lang in ("vi", "en")
        }
        valid = summary["json_valid_after_retry"] or 0
        summary["meets_adr_0004"] = (
            valid >= JSON_VALID_TARGET and (summary["pass_rate"] or 0) >= PASS_TARGET
        )
    return summary


def summarize(results_dir: Path, scores_path: Path) -> dict[str, Any]:
    records = load_records(results_dir)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["provider"], record["model"])].append(record)
    scores = _load_scores(scores_path, "agreed")
    summary = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "models": [summarize_model(grouped[k], scores) for k in sorted(grouped)],
        "grader_agreement": agreement(scores_path, "A", "B"),
    }
    (results_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )
    return summary


def _print_table(summary: dict[str, Any]) -> None:
    columns = (
        "provider",
        "model",
        "pass",
        "clarify ok",
        "no false clarify",
        "JSON 1st",
        "JSON final",
        "retries",
        "median s",
        "max s",
    )
    print("| " + " | ".join(columns) + " |")
    print("|" + "---|" * len(columns))
    for m in summary["models"]:
        cells = (
            m["provider"],
            m["model"],
            m.get("pass_rate", "-"),
            m["clarify_correct"],
            m["no_false_clarification"],
            m["json_first_attempt_valid"],
            m["json_valid_after_retry"],
            m["retries"],
            m["duration_s"]["median"],
            m["duration_s"]["max"],
        )
        print("| " + " | ".join(str(c) for c in cells) + " |")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the pipeline on the samples for one provider/model")
    run.add_argument("--provider", choices=("local", "openai"), required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--samples", nargs="*", default=(), help="sample id prefixes, e.g. 01 07")
    run.add_argument("--base-url", default="http://localhost:11434")
    run.add_argument("--concurrency", type=int, default=0, help="0 = provider default")
    run.add_argument("--timeout", type=float, default=0, help="seconds per call; 0 = default")
    run.add_argument("--max-retries", type=int, default=2)
    run.add_argument("--out-dir", default=str(RESULTS_DIR))
    run.add_argument("--force", action="store_true", help="re-run samples that have results")

    pack = sub.add_parser("grading-pack", help="write blinded plans for graders")
    pack.add_argument("--results-dir", default=str(RESULTS_DIR))
    pack.add_argument("--out-dir", default=str(RESULTS_DIR / "grading"))
    pack.add_argument("--seed", type=int, default=2026)

    merge = sub.add_parser("merge-scores", help="un-blind grader sheets into scores.csv")
    merge.add_argument("--grading-dir", default=str(RESULTS_DIR / "grading"))
    merge.add_argument("--scores", default=str(SCORES_FILE))

    summ = sub.add_parser("summarize", help="aggregate results and agreed scores")
    summ.add_argument("--results-dir", default=str(RESULTS_DIR))
    summ.add_argument("--scores", default=str(SCORES_FILE))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "run":
        if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("OPENAI_API_KEY is not set", file=sys.stderr)
            return 2
        asyncio.run(run_eval(args))
    elif args.command == "grading-pack":
        grading_pack(Path(args.results_dir), Path(args.out_dir), args.seed)
    elif args.command == "merge-scores":
        merge_scores(Path(args.grading_dir), Path(args.scores))
    else:
        _print_table(summarize(Path(args.results_dir), Path(args.scores)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
