"""Dependency-graph checks and the stable priority topological order used by list scheduling."""

import heapq
from collections.abc import Collection, Sequence

from app.scheduler.errors import ScheduleInputError
from app.scheduler.models import SchedulerTask


def validate_references(tasks: Sequence[SchedulerTask], done_task_ids: Collection[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for task in tasks:
        (duplicates if task.id in seen else seen).add(task.id)
    if duplicates:
        ids = tuple(sorted(duplicates))
        raise ScheduleInputError("duplicate_task_id", ids, f"duplicate task ids: {', '.join(ids)}")

    known = seen | set(done_task_ids)
    unknown = sorted({dep for task in tasks for dep in task.depends_on if dep not in known})
    if unknown:
        raise ScheduleInputError(
            "unknown_dependency",
            tuple(unknown),
            f"dependencies reference unknown tasks: {', '.join(unknown)}",
        )


def priority_topological_order(tasks: Sequence[SchedulerTask]) -> list[SchedulerTask]:
    """Kahn's algorithm that always releases the ready task with the smallest ``priority_key``.

    Dependencies on ids outside ``tasks`` (finished tasks) are ignored. Raises
    ``ScheduleInputError`` naming one cycle when the graph is not a DAG.
    """
    by_id = {task.id: task for task in tasks}
    preds = {task.id: {d for d in task.depends_on if d in by_id} for task in tasks}
    succs: dict[str, list[str]] = {task_id: [] for task_id in by_id}
    for task_id, task_preds in preds.items():
        for pred in task_preds:
            succs[pred].append(task_id)

    pending = {task_id: len(task_preds) for task_id, task_preds in preds.items()}
    ready = [by_id[i].priority_key for i, count in pending.items() if count == 0]
    heapq.heapify(ready)
    order: list[SchedulerTask] = []
    while ready:
        task = by_id[heapq.heappop(ready)[3]]
        order.append(task)
        for succ in succs[task.id]:
            pending[succ] -= 1
            if pending[succ] == 0:
                heapq.heappush(ready, by_id[succ].priority_key)

    if len(order) != len(tasks):
        cycle = _find_cycle({i for i, count in pending.items() if count > 0}, preds)
        raise ScheduleInputError(
            "dependency_cycle", cycle, f"dependency cycle: {' -> '.join((*cycle, cycle[0]))}"
        )
    return order


def _find_cycle(remaining: set[str], preds: dict[str, set[str]]) -> tuple[str, ...]:
    """Every node left after Kahn's algorithm has a remaining predecessor, so walking
    predecessors must revisit a node; the walk is made deterministic by picking the smallest id."""
    node = min(remaining)
    path: list[str] = []
    position: dict[str, int] = {}
    while node not in position:
        position[node] = len(path)
        path.append(node)
        node = min(p for p in preds[node] if p in remaining)
    loop = path[position[node] :]
    loop.reverse()
    first = loop.index(min(loop))
    return tuple(loop[first:] + loop[:first])
