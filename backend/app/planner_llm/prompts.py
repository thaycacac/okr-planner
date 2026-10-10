"""Provider-agnostic prompts. Instructions stay in English; output language is explicit."""

import json
from collections.abc import Sequence
from typing import Any

from app.planner_llm.schemas import (
    KeyResultInput,
    KeyResultNeed,
    Language,
    ObjectiveInput,
    OkrInput,
    PlannedTask,
    TimeBudget,
)
from app.planner_llm.validation import (
    MAX_DEDUP_CROSS_DEPENDENCIES,
    MAX_DEDUP_MERGES,
    MAX_TASK_HOURS,
    MIN_TASK_HOURS,
)

_LANGUAGE_NAMES: dict[Language, str] = {"vi": "Vietnamese", "en": "English"}
_MAX_ECHO_CHARS = 4000


def _dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _kr_payload(kr: KeyResultInput) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": kr.id, "text": kr.text}
    for field in ("metric", "unit", "baseline", "target"):
        value = getattr(kr, field)
        if value is not None:
            payload[field] = value
    return payload


def _shared_context(okr: OkrInput) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if okr.context:
        payload["context"] = okr.context
    if okr.clarifications:
        payload["clarifications"] = [
            {"kr_id": a.kr_id, "question": a.question, "answer": a.answer}
            for a in okr.clarifications
        ]
    return payload


def key_result_check_prompt(okr: OkrInput, kr: KeyResultInput) -> tuple[str, str]:
    system = """You judge one key result of an OKR (Objectives and Key Results) before it is \
planned. It is concrete when it states an end result that will exist or happen by the end of \
the quarter: a deliverable or artifact (document, guide, checklist, plan, report, repository, \
release, menu, schedule), an event (a talk given, a test run, a meeting held) or a number to \
reach (a count per week, a value to move from one level to another). It is not concrete when \
it is only a direction with no end result, such as "learn more skills", "improve marketing", \
"get more customers" or "employees are happier". How the work will be done, and details such \
as format, content, reviewers or an exact score, do not matter: planning decides them. \
Answers in "clarifications" count as part of the key result.

First copy into end_result the words that state the end result, or "" if there are none. \
Then set concrete. Respond only with JSON matching the schema."""
    payload: dict[str, Any] = {"key_result": _kr_payload(kr)}
    answers = [
        {"question": a.question, "answer": a.answer}
        for a in okr.clarifications
        if a.kr_id in (kr.id, None)
    ]
    if answers:
        payload["clarifications"] = answers
    return system, _dump(payload)


def clarify_prompt(
    okr: OkrInput, language: Language, vague: Sequence[KeyResultInput]
) -> tuple[str, str]:
    system = f"""You help a person make an OKR (Objectives and Key Results) plannable before \
it is broken down into work tasks for one person over a quarter.

Each key result in "vague_key_results" is a bare direction: it names neither something to \
deliver nor a number to reach. For each of them, ask which concrete deliverable, or which \
metric with its current value and target, is meant.

Rules:
- Exactly one short, specific question per vague key result, with kr_id set to its id.
- Ask only which deliverable or which metric is meant. Never ask how to do the work (steps, \
format, content, tools, what to send to whom, who reviews it): planning decides that.
- Never ask about the other key results in "objectives"; those that already name a deliverable \
or a number are clear.
- Never invent numbers, baselines, targets, dates or facts, and never suggest example values \
in a question.
- Do not ask about anything already answered in "clarifications".
- Use status "needs_clarification".
- Write question and reason in {_LANGUAGE_NAMES[language]}.
Respond only with JSON matching the schema."""
    payload: dict[str, Any] = {
        "objectives": [
            {
                "id": o.id,
                "title": o.title,
                "key_results": [_kr_payload(kr) for kr in o.key_results],
            }
            for o in okr.objectives
        ],
        "vague_key_results": [{"id": kr.id, "text": kr.text} for kr in vague],
        **_shared_context(okr),
    }
    return system, _dump(payload)


def _budget_rule(budget: TimeBudget | None, kr_count: int, max_hours: float | None) -> str:
    if budget is None:
        return ""
    share = round(budget.usable_hours / max(1, kr_count))
    cap = "" if max_hours is None else f" This key result must stay within {max_hours:g} hours."
    return f"""Time budget from the user's calendar: {budget.working_days} working days left in \
the quarter at about {budget.hours_per_day:g} hours per day, {budget.total_hours:g} hours in \
total, {budget.usable_hours:g} hours usable after the schedule buffer. All {kr_count} key \
results of the plan share this budget, about {share} hours each on average.{cap} That is a \
ceiling, not a target: plan the effort the work really needs, which for most key results is \
well below it. If the context states a smaller daily limit, that limit wins.

"""


def decompose_prompt(
    okr: OkrInput,
    objective: ObjectiveInput,
    kr: KeyResultInput,
    language: Language,
    budget: TimeBudget | None = None,
    max_hours: float | None = None,
) -> tuple[str, str]:
    kr_count = sum(len(o.key_results) for o in okr.objectives)
    system = f"""You break one key result into concrete work tasks for a single person over \
one quarter.

{_budget_rule(budget, kr_count, max_hours)}Work in this order:
1. Estimate the real total effort of this key result in hours. Count the concrete work items; \
for repeated work multiply the number of sessions, calls, interviews or items by the time each \
one really takes, which is often one hour or less. This total is not a task.
2. Cover the whole life cycle of the key result, skipping only steps that clearly do not apply:
   a. prepare and define: criteria, scope, template, tools, data or access needed;
   b. do the work, split into batches; when the key result counts items (interviews, calls, \
posts, lessons, deals), each batch task covers 3 to 5 of them, numbered, until all are covered;
   c. check it: test, review, trial with real users or feedback from a reviewer;
   d. revise it based on that check;
   e. hand it over: release, submit, publish, present or roll out;
   f. measure the result.
   When the key result has a metric, measure the baseline before any improvement, track the \
metric during the quarter (for example a mid-quarter check) and measure it again at the end.
3. Split the effort into tasks of {MIN_TASK_HOURS:g} to {MAX_TASK_HOURS:g} hours so that the \
estimates add up to the total from step 1. Any piece of work longer than {MAX_TASK_HOURS:g} \
hours becomes several distinct steps, each with its own output: a 10-hour build is "Build the \
data import" and "Build the summary report"; 9 calls of about an hour are "Calls 1-3", \
"Calls 4-6" and "Calls 7-9" of 3 hours each. Never number tasks as parts ("part 1", \
"phần 2", "(1/2)") and never split a vague job to fill hours: work you cannot name a \
checkable output for is not a task. Never one task for the whole quarter and never one task \
per short session. Fold steps shorter than {MIN_TASK_HOURS:g} hours into a neighbouring task.

Rules:
- Plan only this key result. The other key results are planned separately; do not plan their \
deliverables here. When another key result already covers the preparation (studying, \
practising, building, collecting data), do not repeat it: this key result then needs only its \
own remaining steps, which may be just a few hours.
- local_id: "t1", "t2", ... in execution order, unique.
- depends_on: local_id values from this list whose output this task needs as input. Add a \
dependency only when that is true; independent batches of repeated work do not depend on each \
other. No cycles.
- kr_id: always "{kr.id}".
- estimate_hours: between {MIN_TASK_HOURS:g} and {MAX_TASK_HOURS:g} for every task, never more.
- title: an action verb and a concrete object. description: one short sentence.
- done_criteria: one result someone else can check, and not the title restated: a number \
reached, a document or file produced, a release, a status in a tool, or who approves it. Never \
only "done", "finalized", "improved" or "more stable".
- Waiting time (store review, reviewer feedback) is calendar time, not a task.
- Do not invent metrics, numbers or facts absent from the input; stay generic when unsure.
- Do not schedule dates; only estimate hours.
- Write title, description and done_criteria in {_LANGUAGE_NAMES[language]}.
Respond only with JSON matching the schema."""
    payload: dict[str, Any] = {
        "objective": objective.title,
        "key_result": _kr_payload(kr),
        "other_key_results": [
            {"id": other.id, "text": other.text}
            for o in okr.objectives
            for other in o.key_results
            if other.id != kr.id
        ],
        **_shared_context(okr),
    }
    return system, _dump(payload)


def dedup_prompt(okr: OkrInput, tasks: Sequence[PlannedTask]) -> tuple[str, str]:
    system = f"""You review a quarter plan whose tasks were planned separately for each key \
result. Remove duplicated work and add the missing links between key results.

1. merges: tasks of different key results that produce the same deliverable (the same \
dashboard, template, analysis, document, release or experiment), even when their titles \
differ. keep_id is the task to keep, remove_ids the duplicates to delete. Tasks of the same \
key result are never duplicates of each other. Not duplicates: \
different steps of one deliverable (design, build, test) or batches of repeated work. Never \
remove every task of a key result. At most {MAX_DEDUP_MERGES} merges.
2. cross_dependencies: for the first tasks of each key result, ask which output of another \
key result's task they need before they can start: an analysis needs the collected data, a \
campaign needs the finished release, a team rollout needs the finished guide, a final exam \
needs the last practice round. Add task_id and depends_on_id only when task_id really needs \
the output of depends_on_id; the two tasks always belong to different key results; no \
cycles. At most {MAX_DEDUP_CROSS_DEPENDENCIES} links.

List the clearest cases first. Use only the ids given. Return empty lists when nothing needs \
to change. Respond only with JSON matching the schema."""
    payload = {
        "key_results": [
            {"id": kr.id, "objective_id": o.id, "text": kr.text}
            for o in okr.objectives
            for kr in o.key_results
        ],
        "tasks": [{"id": t.local_id, "kr_id": t.kr_id, "title": t.title} for t in tasks],
    }
    return system, _dump(payload)


def key_result_needs_prompt(okr: OkrInput) -> tuple[str, str]:
    system = """You look at the key results of one person's quarter plan and find the order \
between them. A key result needs another one when part of its work can only be done with a \
concrete output of the other: data, a finished release, a written document, a trained model, \
a submitted paper. Typical cases: an analysis needs the collected or labelled data, a \
marketing campaign needs the finished release, a talk needs the finished results, a team \
rollout needs the finished guide, drills need the written procedures.

Go through the key results one by one and list every such need: kr_id needs needs_kr_id, and \
output names what it needs. Only real needs; key results that are merely related are not \
listed. Never list a key result as needing itself. Respond only with JSON matching the schema."""
    payload = {
        "key_results": [
            {"id": kr.id, "objective": o.title, "text": kr.text}
            for o in okr.objectives
            for kr in o.key_results
        ]
    }
    return system, _dump(payload)


def _link_task(task: PlannedTask) -> dict[str, Any]:
    return {"id": task.local_id, "title": task.title}


def link_prompt(
    need: KeyResultNeed, needing: Sequence[PlannedTask], giving: Sequence[PlannedTask]
) -> tuple[str, str]:
    system = f"""Key result {need.kr_id} needs "{need.output}" from key result \
{need.needs_kr_id}. Link the two plans with one dependency: task_id is the task in \
"needing_tasks" that first needs this output, and depends_on_id is the task in \
"giving_tasks" that produces it. Tasks that come before the need stay unlinked, so the \
earlier work of {need.kr_id} can go ahead in parallel.

Return one link, or an empty list when no task in "needing_tasks" really needs the output. \
Use only the ids given. Respond only with JSON matching the schema."""
    payload = {
        "need": {"kr_id": need.kr_id, "needs_kr_id": need.needs_kr_id, "output": need.output},
        "needing_tasks": [_link_task(t) for t in needing],
        "giving_tasks": [_link_task(t) for t in giving],
    }
    return system, _dump(payload)


def with_feedback(user: str, errors: Sequence[str], previous: dict[str, Any] | None) -> str:
    lines = [
        user,
        "",
        "Your previous answer was rejected. "
        "Fix every problem below and return the full JSON again:",
        *(f"- {e}" for e in errors),
    ]
    if previous is not None:
        echo = json.dumps(previous, ensure_ascii=False)
        if len(echo) > _MAX_ECHO_CHARS:
            echo = echo[:_MAX_ECHO_CHARS] + "…"
        lines += ["", "Previous answer:", echo]
    return "\n".join(lines)
