"""Turns free-text OKRs into structured objectives and key results.

The model only structures what the user wrote; it never invents numbers or dates. Output
models carry no defaults or constraints (strict Structured Outputs); ``normalize`` enforces the
rules afterwards.
"""

import json
from datetime import date
from typing import Literal

from pydantic import BaseModel

MAX_OBJECTIVES = 10
MAX_KEY_RESULTS = 10

Kind = Literal["numeric", "milestone", "binary", "other"]
Priority = Literal["high", "medium", "low"]


class ParsedKr(BaseModel):
    text: str
    kind: Kind
    baseline: float | None
    target: float | None
    unit: str | None
    due_date: str | None
    note: str | None


class ParsedObjective(BaseModel):
    title: str
    priority: Priority
    key_results: list[ParsedKr]


class ParsedOkr(BaseModel):
    objectives: list[ParsedObjective]


SYSTEM = """You structure OKRs that a user typed as free text. Output JSON only.

Rules:
- Keep the user's language and wording. Never translate, never invent objectives, key results,
  numbers or dates that are not in the text.
- An Objective is a goal sentence (often "O1:", "Mục tiêu"); a Key Result is a measurable outcome
  under it (often "KR1:", a bullet, or a sentence that states a target or a deadline). Several
  objectives may appear in one text.
- Key result "text" is the user's sentence without its "KR1:" label.
- kind "numeric": the key result states a measurable amount to reach (clicks, tests, users,
  percent, revenue). Set "target" to that number and "unit" to the thing counted (short, in the
  user's language, e.g. "lượt nhấp", "%"). "baseline" is the starting value if the text gives one,
  otherwise 0. Ignore numbers that are only a duration or period (e.g. "in 28 days").
- kind "milestone": a single thing to finish by a date. Set "due_date" as YYYY-MM-DD.
- kind "binary": done or not done, no date and no amount.
- kind "other": everything else, including habits over a period ("every day from X to Y"). Put
  any useful detail in "note", else null.
- Fields that do not apply to the kind are null. "due_date" only for milestone.
- A date without a year belongs to the year of the quarter given below; day/month order is
  day first (20/10 is 20 October).
- priority is "medium" unless the text states otherwise."""


def okr_parse_prompt(text: str, start: date, end: date) -> tuple[str, str]:
    user = json.dumps(
        {"quarter_start": start.isoformat(), "quarter_end": end.isoformat(), "text": text},
        ensure_ascii=False,
    )
    return SYSTEM, user


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _in_quarter(value: str | None, start: date, end: date) -> str | None:
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return parsed.isoformat() if start <= parsed <= end else None


def normalize(parsed: ParsedOkr, start: date, end: date) -> ParsedOkr:
    """Drops empty items, repairs kind/field mismatches and applies the count limits."""
    objectives: list[ParsedObjective] = []
    for objective in parsed.objectives:
        title = objective.title.strip()
        krs: list[ParsedKr] = []
        for kr in objective.key_results:
            text = kr.text.strip()
            if not text:
                continue
            kind: Kind = kr.kind
            due = _in_quarter(kr.due_date, start, end)
            if kind == "numeric" and kr.target is None:
                kind = "other"
            if kind == "milestone" and due is None:
                kind = "other"
            numeric = kind == "numeric"
            krs.append(
                ParsedKr(
                    text=text,
                    kind=kind,
                    baseline=(kr.baseline if kr.baseline is not None else 0.0) if numeric else None,
                    target=kr.target if numeric else None,
                    unit=_clean(kr.unit) if numeric else None,
                    due_date=due if kind == "milestone" else None,
                    note=_clean(kr.note) if kind == "other" else None,
                )
            )
        if not title and not krs:
            continue
        objectives.append(
            ParsedObjective(
                title=title, priority=objective.priority, key_results=krs[:MAX_KEY_RESULTS]
            )
        )
    return ParsedOkr(objectives=objectives[:MAX_OBJECTIVES])
