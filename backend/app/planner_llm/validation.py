"""Rule checks on LLM output. Every message is phrased so the model can fix it on retry.

Messages reference ids and numbers only, never titles or OKR text.
"""

import math
import re
import unicodedata
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from typing import Protocol

from app.planner_llm.schemas import (
    ClarifyOutput,
    DecomposeOutput,
    DedupOutput,
    KeyResultNeedsOutput,
    LinkOutput,
    PlannedTask,
)

MIN_TASK_HOURS = 2.0
MAX_TASK_HOURS = 6.0
MAX_TASKS_PER_KR = 25
MAX_QUESTIONS = 5
# A heavy key result may take more than an equal share of the quarter, but not without bound.
KR_SHARE_CEILING = 1.5
MAX_DEDUP_MERGES = 5
MAX_DEDUP_CROSS_DEPENDENCIES = 8


class TaskLike(Protocol):
    @property
    def local_id(self) -> str: ...
    @property
    def kr_id(self) -> str: ...
    @property
    def title(self) -> str: ...
    @property
    def done_criteria(self) -> str: ...
    @property
    def estimate_hours(self) -> float: ...
    @property
    def depends_on(self) -> Sequence[str]: ...


def find_cycle(graph: Mapping[str, Sequence[str]]) -> list[str] | None:
    """Return one dependency cycle as ``[a, b, ..., a]``, or ``None`` if the graph is acyclic.

    Edges pointing outside ``graph`` are ignored; report them separately.
    """
    visiting, done = 1, 2
    state: dict[str, int] = {}
    for root in graph:
        if root in state:
            continue
        state[root] = visiting
        path = [root]
        stack = [iter(graph[root])]
        while stack:
            nxt = next(stack[-1], None)
            if nxt is None:
                stack.pop()
                state[path.pop()] = done
                continue
            if nxt not in graph:
                continue
            seen = state.get(nxt)
            if seen == visiting:
                return [*path[path.index(nxt) :], nxt]
            if seen is None:
                state[nxt] = visiting
                path.append(nxt)
                stack.append(iter(graph[nxt]))
    return None


def task_graph_errors(
    tasks: Sequence[TaskLike],
    *,
    allowed_kr_ids: Collection[str],
    required_kr_ids: Collection[str],
) -> list[str]:
    errors: list[str] = []
    ids: list[str] = [t.local_id for t in tasks]
    id_set = set(ids)

    if len(id_set) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errors.append(f"local_id values must be unique; duplicated: {', '.join(dupes)}")

    for task in tasks:
        tid = task.local_id or "<empty>"
        if not task.local_id.strip():
            errors.append("every task needs a non-empty local_id")
        if task.kr_id not in allowed_kr_ids:
            allowed = ", ".join(sorted(allowed_kr_ids))
            errors.append(f"task {tid}: kr_id '{task.kr_id}' is not valid; use one of: {allowed}")
        if not task.title.strip():
            errors.append(f"task {tid}: title must not be empty")
        if not task.done_criteria.strip():
            errors.append(f"task {tid}: done_criteria must not be empty")
        hours = task.estimate_hours
        if hours > MAX_TASK_HOURS:
            errors.append(
                f"task {tid}: estimate_hours {hours:g} is above {MAX_TASK_HOURS:g}; "
                f"split it into smaller tasks of {MIN_TASK_HOURS:g}-{MAX_TASK_HOURS:g} hours"
            )
        elif hours < MIN_TASK_HOURS:
            errors.append(
                f"task {tid}: estimate_hours {hours:g} is below {MIN_TASK_HOURS:g}; "
                "merge it into a related task or widen its scope"
            )
        for dep in task.depends_on:
            if dep == task.local_id:
                errors.append(f"task {tid}: must not depend on itself")
            elif dep not in id_set:
                errors.append(f"task {tid}: depends_on '{dep}' is not a local_id in this plan")

    cycle = find_cycle({t.local_id: list(t.depends_on) for t in tasks})
    if cycle:
        errors.append(f"dependency cycle {' -> '.join(cycle)}; remove one of these dependencies")

    covered = {t.kr_id for t in tasks}
    missing = [kr for kr in required_kr_ids if kr not in covered]
    if missing:
        errors.append(f"every key result needs at least one task; missing: {', '.join(missing)}")
    return errors


def clarify_errors(
    output: ClarifyOutput, kr_ids: Collection[str], required: Collection[str] = ()
) -> list[str]:
    """``required`` lists key results that need a question; one about the whole OKR covers all."""
    errors: list[str] = []
    asked = {q.kr_id for q in output.questions}
    if None not in asked:
        errors.extend(
            f"key result {kr_id} has no question; ask one about it"
            for kr_id in required
            if kr_id not in asked
        )
    if output.status == "needs_clarification" and not output.questions:
        errors.append("status is needs_clarification but questions is empty; add questions")
    if output.status == "ok" and output.questions:
        errors.append(
            "status is ok but questions is not empty; use status needs_clarification "
            "to ask them, or return an empty questions list"
        )
    if output.status == "needs_clarification":
        for i, question in enumerate(output.questions, start=1):
            if not question.question.strip():
                errors.append(f"question {i}: text must not be empty")
            if question.kr_id is not None and question.kr_id not in kr_ids:
                errors.append(
                    f"question {i}: kr_id '{question.kr_id}' is unknown; "
                    "use a given key result id or null"
                )
    return errors


def ok_with_questions_as_clarification(
    output: ClarifyOutput, kr_ids: Collection[str]
) -> ClarifyOutput | None:
    """Read ``ok`` plus valid questions as ``needs_clarification``; ``None`` otherwise.

    Used once retries are spent: asking back is safer than dropping questions the model wrote.
    """
    if output.status != "ok" or not output.questions:
        return None
    asking = output.model_copy(update={"status": "needs_clarification"})
    return None if clarify_errors(asking, kr_ids) else asking


def decompose_errors(output: DecomposeOutput, kr_id: str) -> list[str]:
    if not output.tasks:
        return ["tasks is empty; return at least one task for this key result"]
    errors: list[str] = []
    if len(output.tasks) > MAX_TASKS_PER_KR:
        errors.append(
            f"{len(output.tasks)} tasks is too many; keep at most {MAX_TASKS_PER_KR} per key result"
        )
    errors.extend(task_graph_errors(output.tasks, allowed_kr_ids={kr_id}, required_kr_ids=[kr_id]))
    return errors


# ---------------------------------------------------------------------------
# Plan quality rules: retried like any rule, but once retries run out the pipeline keeps the
# last structurally valid plan instead of failing it, because they judge effort and wording
# rather than whether the plan can be scheduled at all. Switch one off in
# ``TASK_QUALITY_RULES`` or by passing ``max_hours=None``.
# ---------------------------------------------------------------------------


def plan_quality_errors(tasks: Sequence[TaskLike], max_hours: float | None) -> list[str]:
    errors = task_quality_errors(tasks)
    if max_hours is not None:
        errors.extend(kr_hours_errors(tasks, max_hours))
    return errors


# Time budget: the quarter's usable hours bound each key result and the whole plan.


def kr_hours_cap(usable_hours: float, kr_count: int) -> float:
    """Most hours one key result may take on the first pass, in whole hours."""
    share = usable_hours / max(1, kr_count)
    return max(MIN_TASK_HOURS, float(math.floor(min(usable_hours, share * KR_SHARE_CEILING))))


def kr_hours_errors(tasks: Sequence[TaskLike], max_hours: float) -> list[str]:
    total = sum(t.estimate_hours for t in tasks)
    if total <= max_hours:
        return []
    return [
        f"estimates add up to {total:g} hours, above the {max_hours:g} hours this key result "
        f"may use; cut at least {total - max_hours:g} hours by dropping or merging the least "
        "important tasks, not by lowering estimates below the real effort"
    ]


def rebalance_caps(hours_by_kr: Mapping[str, float], usable_hours: float) -> dict[str, float]:
    """New caps for the key results to re-plan when the plan exceeds ``usable_hours``.

    Only key results above an equal share are cut, each in proportion to how far it is above
    that share, so the caps add up to the budget and light key results stay untouched.
    Empty when the plan already fits.
    """
    total = sum(hours_by_kr.values())
    if not hours_by_kr or total <= usable_hours:
        return {}
    share = usable_hours / len(hours_by_kr)
    above = {kr: hours - share for kr, hours in hours_by_kr.items() if hours > share}
    excess = total - usable_hours
    weight = sum(above.values())
    return {
        kr: max(MIN_TASK_HOURS, float(math.floor(hours_by_kr[kr] - excess * over / weight)))
        for kr, over in above.items()
    }


# Task quality: padding tasks and done criteria nobody can check.


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


_PART_WORD = re.compile(r"\b(?:part|phần)\s*(?:\d+|one|two|three|một|hai|ba)\b", re.IGNORECASE)
_PART_FRACTION = re.compile(
    r"\(\s*(\d+)\s*/\s*(\d+)\s*\)|\b(\d+)\s*(?:/|\s(?:of|trên)\s)\s*(\d+)\s*$", re.IGNORECASE
)
_MAX_PARTS = 12
_TRAILING_NUMBER = re.compile(r"^(?P<stem>.*?)(?:\s+(?:no|so))?\s+(?P<number>\d+)$")
# Work numbered by batch, period or variant ("interviews batch 2", "đợt 2", "phương án 2") is
# not padding.
_BATCH_WORDS = _words(
    "batch round wave week month sprint session lesson chapter module cohort group exam test "
    "iteration variant version option prototype "
    "dot vong luot lan buoi tuan thang bai chuong nhom an ban mau"
)
_STOPWORDS = _words(
    "a an the of for to and or in on at by with from into is are be been being was were has "
    "have had it its this that these those as all any each per so if when needed necessary "
    "va la cua cho cac nhung mot voi trong theo ve bang de da duoc dang se khi neu can tat ca "
    "nay do"
)
# Completion and improvement words that say nothing observable on their own (folded,
# five-letter stems for English).
_GENERIC_STEMS = _words(
    "compl done finis final ready optim impro stabl bette enhan adjus succe effec achie updat "
    "made make more less fully prope "
    "xong hoan thanh toi uu on dinh hon tot cai thien hieu qua dieu chinh san sang cong nang "
    "cao cap nhat"
)
_HIGH_OVERLAP = 0.85


def _fold(text: str) -> str:
    """Lower case without Vietnamese marks, words separated by single spaces."""
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _stems(text: str) -> list[str]:
    """Content words of ``text`` cut to five letters, a crude stem that matches word forms."""
    return [w[:5] for w in _fold(text).split() if w not in _STOPWORDS]


def _is_part_title(title: str) -> bool:
    if _PART_WORD.search(title):
        return True
    match = _PART_FRACTION.search(title)
    if not match:
        return False
    part, of = (int(n) for n in match.groups() if n is not None)
    return 1 <= part <= of <= _MAX_PARTS


def part_title_errors(tasks: Sequence[TaskLike]) -> list[str]:
    return [
        f"task {t.local_id}: title is numbered as a part (part 1, phần 2, (1/2)); do not split "
        "one job into parts, give each task its own concrete output"
        for t in tasks
        if _is_part_title(t.title)
    ]


def numbered_sibling_errors(tasks: Sequence[TaskLike]) -> list[str]:
    groups: dict[tuple[str, str], list[str]] = {}
    for task in tasks:
        match = _TRAILING_NUMBER.match(_fold(task.title))
        if not match or not match["stem"]:
            continue
        last_word = match["stem"].rsplit(" ", 1)[-1]
        if last_word in _BATCH_WORDS:
            continue
        groups.setdefault((task.kr_id, match["stem"]), []).append(task.local_id)
    return [
        f"tasks {', '.join(ids)} differ only by a trailing number; give each task its own "
        "concrete output or merge them into one task"
        for ids in groups.values()
        if len(ids) > 1
    ]


def unverifiable_done_criteria_errors(tasks: Sequence[TaskLike]) -> list[str]:
    errors: list[str] = []
    for task in tasks:
        done = _stems(task.done_criteria)
        if not done:
            continue
        title = set(_stems(task.title))
        novel = [s for s in done if s not in title and s not in _GENERIC_STEMS]
        overlap = sum(1 for s in done if s in title) / len(done)
        if novel and overlap < _HIGH_OVERLAP:
            continue
        errors.append(
            f"task {task.local_id}: done_criteria only repeats the title or says done, "
            "finalized, improved or more stable; state one observable result: a number, a "
            "document, a release, a status or who approves it"
        )
    return errors


TaskRule = Callable[[Sequence[TaskLike]], list[str]]
TASK_QUALITY_RULES: dict[str, TaskRule] = {
    "part_title": part_title_errors,
    "numbered_siblings": numbered_sibling_errors,
    "unverifiable_done_criteria": unverifiable_done_criteria_errors,
}


def task_quality_errors(
    tasks: Sequence[TaskLike], rules: Mapping[str, TaskRule] = TASK_QUALITY_RULES
) -> list[str]:
    return [error for rule in rules.values() for error in rule(tasks)]


def namespace_tasks(output: DecomposeOutput, *, kr_id: str, objective_id: str) -> list[PlannedTask]:
    """Rename ids to ``<kr_id>.t<n>`` so they stay unique once KRs are combined."""
    mapping = {task.local_id: f"{kr_id}.t{i}" for i, task in enumerate(output.tasks, start=1)}
    return [
        PlannedTask(
            local_id=mapping[task.local_id],
            objective_id=objective_id,
            kr_id=kr_id,
            title=task.title.strip(),
            description=task.description.strip(),
            estimate_hours=task.estimate_hours,
            done_criteria=task.done_criteria.strip(),
            depends_on=_unique(mapping[d] for d in task.depends_on),
        )
        for task in output.tasks
    ]


def _unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _dependency_linked_pair(
    group: Sequence[str], by_id: Mapping[str, PlannedTask]
) -> tuple[str, str] | None:
    """Return ``(later, earlier)`` if one task of ``group`` transitively depends on another."""
    members = set(group)
    for start in group:
        seen: set[str] = set()
        frontier = list(by_id[start].depends_on)
        while frontier:
            dep = frontier.pop()
            if dep in seen or dep not in by_id:
                continue
            if dep in members:
                return start, dep
            seen.add(dep)
            frontier.extend(by_id[dep].depends_on)
    return None


def need_errors(output: KeyResultNeedsOutput, kr_ids: Collection[str]) -> list[str]:
    errors: list[str] = []
    for i, need in enumerate(output.needs, start=1):
        unknown = [k for k in (need.kr_id, need.needs_kr_id) if k not in kr_ids]
        if unknown:
            errors.append(f"need {i}: unknown key result ids {', '.join(unknown)}")
        elif need.kr_id == need.needs_kr_id:
            errors.append(f"need {i}: a key result cannot need itself")
    return errors


def link_errors(output: LinkOutput, needing: Collection[str], giving: Collection[str]) -> list[str]:
    if len(output.links) > 1:
        return ["return at most one link"]
    errors: list[str] = []
    for link in output.links:
        if link.task_id not in needing:
            errors.append(f"task_id '{link.task_id}' is not one of needing_tasks")
        if link.depends_on_id not in giving:
            errors.append(f"depends_on_id '{link.depends_on_id}' is not one of giving_tasks")
    return errors


def apply_dedup(
    tasks: Sequence[PlannedTask], output: DedupOutput, kr_ids: Collection[str]
) -> tuple[list[PlannedTask], list[str]]:
    """Apply merges and cross-KR dependencies; return the new list or the errors found."""
    errors: list[str] = []
    by_id = {t.local_id: t for t in tasks}
    replaced_by: dict[str, str] = {}
    claimed: set[str] = set()

    for i, merge in enumerate(output.merges, start=1):
        group = [merge.keep_id, *merge.remove_ids]
        unknown = [tid for tid in group if tid not in by_id]
        if unknown:
            errors.append(f"merge {i}: unknown task ids {', '.join(unknown)}")
            continue
        if merge.keep_id in merge.remove_ids:
            errors.append(f"merge {i}: keep_id {merge.keep_id} must not be in remove_ids")
            continue
        overlap = [tid for tid in group if tid in claimed]
        if overlap:
            errors.append(f"merge {i}: ids {', '.join(overlap)} already appear in another merge")
            continue
        linked = _dependency_linked_pair(group, by_id)
        if linked:
            later, earlier = linked
            errors.append(
                f"merge {i}: {later} depends on {earlier}, so they are consecutive steps, "
                "not duplicates; do not merge them"
            )
            continue
        claimed.update(group)
        for tid in merge.remove_ids:
            replaced_by[tid] = merge.keep_id

    def resolve(tid: str) -> str:
        return replaced_by.get(tid, tid)

    kept = [t for t in tasks if t.local_id not in replaced_by]
    covered = {t.kr_id for t in kept}
    emptied = [kr for kr in kr_ids if kr not in covered]
    if emptied:
        errors.append(
            f"merges remove every task of key result {', '.join(emptied)}; "
            "keep at least one task per key result"
        )

    extra_deps: dict[str, list[str]] = {}
    for tid, keep_id in replaced_by.items():
        extra_deps.setdefault(keep_id, []).extend(by_id[tid].depends_on)
    for i, dep in enumerate(output.cross_dependencies, start=1):
        unknown = [tid for tid in (dep.task_id, dep.depends_on_id) if tid not in by_id]
        if unknown:
            errors.append(f"cross_dependency {i}: unknown task ids {', '.join(unknown)}")
            continue
        extra_deps.setdefault(resolve(dep.task_id), []).append(dep.depends_on_id)

    if errors:
        return list(tasks), errors

    result: list[PlannedTask] = []
    for task in kept:
        deps = _unique(
            resolve(d)
            for d in [*task.depends_on, *extra_deps.get(task.local_id, [])]
            if resolve(d) != task.local_id
        )
        result.append(task.model_copy(update={"depends_on": deps}))

    cycle = find_cycle({t.local_id: t.depends_on for t in result})
    if cycle:
        return list(tasks), [
            f"cross_dependencies create a cycle {' -> '.join(cycle)}; remove one of them"
        ]
    return result, []
