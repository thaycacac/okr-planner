"""Deterministic checks that run before any LLM call."""

import re
from dataclasses import dataclass

from app.planner_llm.schemas import KeyResultInput, Language, OkrInput, PrecheckIssue

MAX_OBJECTIVES = 10
MAX_KEY_RESULTS_PER_OBJECTIVE = 10
MIN_TEXT_LENGTH = 5
MAX_OBJECTIVE_LENGTH = 300
MAX_KR_LENGTH = 500
MAX_CONTEXT_LENGTH = 4000
MAX_ANSWER_LENGTH = 1000

_MESSAGES: dict[str, tuple[str, str]] = {
    "no_objectives": ("Cần ít nhất một Objective.", "At least one objective is required."),
    "too_many_objectives": (
        f"Tối đa {MAX_OBJECTIVES} Objective mỗi lần lập kế hoạch.",
        f"At most {MAX_OBJECTIVES} objectives per plan.",
    ),
    "objective_too_short": (
        f"Objective cần ít nhất {MIN_TEXT_LENGTH} ký tự.",
        f"Objective needs at least {MIN_TEXT_LENGTH} characters.",
    ),
    "objective_too_long": (
        f"Objective dài quá {MAX_OBJECTIVE_LENGTH} ký tự.",
        f"Objective is longer than {MAX_OBJECTIVE_LENGTH} characters.",
    ),
    "no_key_results": ("Objective cần ít nhất một KR.", "Objective needs at least one key result."),
    "too_many_key_results": (
        f"Tối đa {MAX_KEY_RESULTS_PER_OBJECTIVE} KR mỗi Objective.",
        f"At most {MAX_KEY_RESULTS_PER_OBJECTIVE} key results per objective.",
    ),
    "kr_too_short": (
        f"KR cần ít nhất {MIN_TEXT_LENGTH} ký tự.",
        f"Key result needs at least {MIN_TEXT_LENGTH} characters.",
    ),
    "kr_too_long": (
        f"KR dài quá {MAX_KR_LENGTH} ký tự.",
        f"Key result is longer than {MAX_KR_LENGTH} characters.",
    ),
    "duplicate_id": ("Mã Objective/KR bị trùng.", "Duplicate objective or key result id."),
    "duplicate_kr": (
        "KR trùng nội dung với một KR khác.",
        "Key result has the same text as another key result.",
    ),
    "context_too_long": (
        f"Bối cảnh dài quá {MAX_CONTEXT_LENGTH} ký tự.",
        f"Context is longer than {MAX_CONTEXT_LENGTH} characters.",
    ),
    "answer_too_long": (
        f"Câu trả lời dài quá {MAX_ANSWER_LENGTH} ký tự.",
        f"Answer is longer than {MAX_ANSWER_LENGTH} characters.",
    ),
}

_CHANGE_WORDS = re.compile(
    r"\b(tăng|giảm|nâng|cải thiện|rút ngắn|increase|decrease|reduce|grow|improve|raise|"
    r"lower|cut|boost)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_NON_WORD = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class MetricGap:
    kr_id: str
    question: str
    reason: str


@dataclass(frozen=True)
class PrecheckResult:
    issues: list[PrecheckIssue]
    metric_gaps: list[MetricGap]


def _issue(
    code: str, language: Language, *, objective_id: str | None = None, kr_id: str | None = None
) -> PrecheckIssue:
    vi, en = _MESSAGES[code]
    return PrecheckIssue(
        code=code,
        message=vi if language == "vi" else en,
        objective_id=objective_id,
        kr_id=kr_id,
    )


def normalize_text(text: str) -> str:
    return _SPACES.sub(" ", _NON_WORD.sub(" ", text.casefold())).strip()


def _short(text: str, limit: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def metric_gap(kr: KeyResultInput, language: Language) -> MetricGap | None:
    """Flag measurable KRs that miss a baseline or target.

    A number in the text counts as the target; two numbers count as baseline and target.
    Relative changes ("increase", "giảm") and structured metrics also need a baseline.
    """
    structured = any(v is not None for v in (kr.metric, kr.unit, kr.baseline, kr.target))
    relative = _CHANGE_WORDS.search(kr.text) is not None
    if not (structured or relative or "%" in kr.text):
        return None
    numbers = len(_NUMBER.findall(kr.text))
    has_target = kr.target is not None or numbers >= 1
    has_baseline = kr.baseline is not None or numbers >= 2
    need_baseline = structured or relative
    missing_target = not has_target
    missing_baseline = need_baseline and not has_baseline
    if not (missing_target or missing_baseline):
        return None

    ref = _short(kr.text)
    if missing_target and missing_baseline:
        vi = f"KR “{ref}” đo bằng chỉ số nào, giá trị hiện tại (baseline) và mục tiêu là bao nhiêu?"
        en = f"For “{ref}”, which metric is measured, and what are the baseline and target?"
        reason = ("Thiếu baseline và target.", "Missing baseline and target.")
    elif missing_baseline:
        vi = f"Giá trị hiện tại (baseline) của KR “{ref}” là bao nhiêu?"
        en = f"What is the current baseline for “{ref}”?"
        reason = ("Thiếu baseline.", "Missing baseline.")
    else:
        vi = f"Mục tiêu cụ thể (target) của KR “{ref}” là bao nhiêu?"
        en = f"What is the concrete target for “{ref}”?"
        reason = ("Thiếu target.", "Missing target.")
    is_vi = language == "vi"
    return MetricGap(
        kr_id=kr.id,
        question=vi if is_vi else en,
        reason=reason[0] if is_vi else reason[1],
    )


def run_precheck(okr: OkrInput, language: Language) -> PrecheckResult:
    issues: list[PrecheckIssue] = []
    gaps: list[MetricGap] = []

    if not okr.objectives:
        issues.append(_issue("no_objectives", language))
    if len(okr.objectives) > MAX_OBJECTIVES:
        issues.append(_issue("too_many_objectives", language))
    if okr.context and len(okr.context) > MAX_CONTEXT_LENGTH:
        issues.append(_issue("context_too_long", language))
    for answer in okr.clarifications:
        if len(answer.answer) > MAX_ANSWER_LENGTH:
            issues.append(_issue("answer_too_long", language, kr_id=answer.kr_id))

    answered_krs = {a.kr_id for a in okr.clarifications if a.kr_id and a.answer.strip()}
    seen_ids: set[str] = set()
    seen_texts: dict[str, str] = {}

    for objective in okr.objectives:
        oid = objective.id
        if oid in seen_ids:
            issues.append(_issue("duplicate_id", language, objective_id=oid))
        seen_ids.add(oid)
        title = objective.title.strip()
        if len(title) < MIN_TEXT_LENGTH:
            issues.append(_issue("objective_too_short", language, objective_id=oid))
        elif len(title) > MAX_OBJECTIVE_LENGTH:
            issues.append(_issue("objective_too_long", language, objective_id=oid))
        if not objective.key_results:
            issues.append(_issue("no_key_results", language, objective_id=oid))
        if len(objective.key_results) > MAX_KEY_RESULTS_PER_OBJECTIVE:
            issues.append(_issue("too_many_key_results", language, objective_id=oid))

        for kr in objective.key_results:
            if kr.id in seen_ids:
                issues.append(_issue("duplicate_id", language, objective_id=oid, kr_id=kr.id))
            seen_ids.add(kr.id)
            text = kr.text.strip()
            if len(text) < MIN_TEXT_LENGTH:
                issues.append(_issue("kr_too_short", language, objective_id=oid, kr_id=kr.id))
                continue
            if len(text) > MAX_KR_LENGTH:
                issues.append(_issue("kr_too_long", language, objective_id=oid, kr_id=kr.id))
                continue
            normalized = normalize_text(text)
            if normalized in seen_texts:
                issues.append(_issue("duplicate_kr", language, objective_id=oid, kr_id=kr.id))
                continue
            seen_texts[normalized] = kr.id
            if kr.id not in answered_krs:
                gap = metric_gap(kr, language)
                if gap:
                    gaps.append(gap)

    return PrecheckResult(issues=issues, metric_gaps=gaps)
