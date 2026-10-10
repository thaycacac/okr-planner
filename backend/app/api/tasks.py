"""Manual task editing: create, edit, delete, move/pin, complete.

Edits never touch the stored schedule; the quarter becomes ``stale`` until it is rescheduled.
"""

from datetime import date

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import Db
from app.api.errors import ApiError, error_responses, not_found
from app.api.schemas import TaskCreate, TaskOut, TaskPinRequest, TaskStatus, TaskUpdate
from app.persistence.models import (
    KeyResult,
    Objective,
    Quarter,
    Task,
    TaskDependency,
    TaskPin,
    utcnow,
)
from app.services.scheduling import (
    CalendarInputs,
    PinError,
    check_pin_days,
    fill_pin_days,
    latest_schedule,
)

router = APIRouter(tags=["tasks"])
NOT_FOUND = error_responses(404)
EDIT_ERRORS = error_responses(404, 409, 422)
_EDIT_FIELDS = ("title", "description", "done_criteria", "estimate_minutes", "key_result_id")


def _task(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise not_found("task", task_id)
    return task


def _key_result(session: Session, kr_id: int) -> KeyResult:
    kr = session.get(KeyResult, kr_id)
    if kr is None:
        raise not_found("key result", kr_id)
    return kr


def _quarter_task_ids(session: Session, quarter_id: int) -> set[int]:
    return set(
        session.scalars(
            select(Task.id)
            .join(Task.key_result)
            .join(KeyResult.objective)
            .where(Objective.quarter_id == quarter_id)
        ).all()
    )


def _dependency_graph(session: Session, task_ids: set[int]) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = {t: set() for t in task_ids}
    rows = session.execute(
        select(TaskDependency.task_id, TaskDependency.depends_on_id).where(
            TaskDependency.task_id.in_(task_ids)
        )
    ).all()
    for task_id, depends_on_id in rows:
        graph[task_id].add(depends_on_id)
    return graph


def _find_path(graph: dict[int, set[int]], start: int, goal: int) -> list[int] | None:
    """Dependency path ``start → … → goal``, walking smallest ids first for stable messages."""
    stack: list[tuple[int, list[int]]] = [(start, [start])]
    seen: set[int] = set()
    while stack:
        node, path = stack.pop()
        if node == goal:
            return path
        if node in seen:
            continue
        seen.add(node)
        for nxt in sorted(graph.get(node, ()), reverse=True):
            stack.append((nxt, [*path, nxt]))
    return None


def _checked_dependencies(
    session: Session, quarter_id: int, task_id: int | None, depends_on: list[int]
) -> list[int]:
    wanted = sorted(set(depends_on))
    if task_id is not None and task_id in wanted:
        raise ApiError(422, "dependency_on_itself", "a task cannot depend on itself")
    known = _quarter_task_ids(session, quarter_id)
    unknown = [d for d in wanted if d not in known]
    if unknown:
        raise ApiError(
            422,
            "unknown_dependency",
            f"tasks not in this quarter: {', '.join(map(str, unknown))}",
        )
    if task_id is not None:
        graph = _dependency_graph(session, known)
        graph[task_id] = set(wanted)
        for dep in wanted:
            path = _find_path(graph, dep, task_id)
            if path is not None:
                chain = " -> ".join(map(str, [task_id, *path]))
                raise ApiError(422, "dependency_cycle", f"dependency cycle: {chain}")
    return wanted


def _set_dependencies(session: Session, task: Task, depends_on: list[int]) -> None:
    task.dependencies.clear()
    session.flush()
    task.dependencies.extend(TaskDependency(depends_on_id=d) for d in depends_on)


def _set_pins(session: Session, task: Task, days: list[tuple[date, int]]) -> None:
    task.pins.clear()
    session.flush()
    task.pins.extend(TaskPin(date=d, minutes=m) for d, m in days)
    task.pinned = True


def _pin_error(exc: PinError) -> ApiError:
    return ApiError(422, exc.code, str(exc))


def _quarter_of(kr: KeyResult) -> Quarter:
    return kr.objective.quarter


@router.post(
    "/key-results/{kr_id}/tasks", status_code=status.HTTP_201_CREATED, responses=EDIT_ERRORS
)
def create_task(kr_id: int, body: TaskCreate, session: Db) -> TaskOut:
    kr = _key_result(session, kr_id)
    depends_on = _checked_dependencies(session, kr.objective.quarter_id, None, body.depends_on)
    position = body.position
    if position is None:
        current = session.scalar(select(func.max(Task.position)).where(Task.key_result_id == kr_id))
        position = 0 if current is None else int(current) + 1
    task = Task(
        key_result_id=kr_id,
        title=body.title.strip(),
        description=body.description.strip(),
        done_criteria=body.done_criteria.strip(),
        estimate_minutes=body.estimate_minutes,
        position=position,
        user_edited=True,
        dependencies=[TaskDependency(depends_on_id=d) for d in depends_on],
    )
    session.add(task)
    session.commit()
    return TaskOut.model_validate(task)


@router.get("/tasks/{task_id}", responses=NOT_FOUND)
def get_task(task_id: int, session: Db) -> TaskOut:
    return TaskOut.model_validate(_task(session, task_id))


@router.patch("/tasks/{task_id}", responses=EDIT_ERRORS)
def update_task(task_id: int, body: TaskUpdate, session: Db) -> TaskOut:
    """A pinned task whose estimate changes is re-pinned from its first pinned day."""
    task = _task(session, task_id)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None:
            raise ApiError(422, "field_required", f"{field} cannot be null")
    quarter = _quarter_of(task.key_result)

    if "key_result_id" in changes and changes["key_result_id"] != task.key_result_id:
        target = _key_result(session, changes["key_result_id"])
        if target.objective.quarter_id != quarter.id:
            raise ApiError(
                422, "key_result_not_in_quarter", "a task can only move within its quarter"
            )
    if "depends_on" in changes:
        depends_on = _checked_dependencies(session, quarter.id, task.id, changes["depends_on"])
        if depends_on != task.depends_on:
            _set_dependencies(session, task, depends_on)
            task.user_edited = True

    estimate = changes.get("estimate_minutes")
    if estimate is not None and estimate != task.estimate_minutes and task.pinned and task.pins:
        try:
            days = fill_pin_days(task.pins[0].date, estimate, CalendarInputs(session, quarter))
        except PinError as exc:
            raise _pin_error(exc) from None
        _set_pins(session, task, list(days))

    for field in _EDIT_FIELDS:
        if field in changes:
            value = changes[field]
            value = value.strip() if isinstance(value, str) else value
            if value != getattr(task, field):
                setattr(task, field, value)
                task.user_edited = True
    if "position" in changes:
        task.position = changes["position"]
    new_status = TaskStatus(changes.get("status", task.status)).value
    if new_status != task.status:
        task.status = new_status
        task.completed_at = utcnow() if new_status == TaskStatus.done else None
    session.commit()
    session.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_task(task_id: int, session: Db, with_dependents: bool = False) -> Response:
    """Dependents lose the link by default; ``with_dependents`` deletes them too (transitively)."""
    task = _task(session, task_id)
    doomed = {task.id}
    if with_dependents:
        quarter_ids = _quarter_task_ids(session, task.key_result.objective.quarter_id)
        graph = _dependency_graph(session, quarter_ids)
        grew = True
        while grew:
            extra = {t for t, deps in graph.items() if deps & doomed and t not in doomed}
            doomed |= extra
            grew = bool(extra)
    for doomed_id in sorted(doomed):
        session.delete(session.get_one(Task, doomed_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/tasks/{task_id}/pin", responses=EDIT_ERRORS)
def pin_task(task_id: int, body: TaskPinRequest, session: Db) -> TaskOut:
    """Moves the task and pins it; a pin may overfill a day, which reschedule reports."""
    task = _task(session, task_id)
    if task.status == TaskStatus.done:
        raise ApiError(409, "task_done", "a finished task cannot be pinned")
    quarter = _quarter_of(task.key_result)
    calendar = CalendarInputs(session, quarter)
    days: list[tuple[date, int]]
    try:
        if body.start_date is not None:
            days = list(fill_pin_days(body.start_date, task.estimate_minutes, calendar))
        elif body.allocations is not None:
            explicit = [(a.date, a.minutes) for a in body.allocations]
            check_pin_days(explicit, task.estimate_minutes, calendar)
            days = list(explicit)
        else:
            run = latest_schedule(session, quarter.id)
            current = [
                (a.date, a.minutes)
                for a in (run.allocations if run else [])
                if a.task_id == task.id and not a.done
            ]
            if sum(m for _, m in current) != task.estimate_minutes:
                raise ApiError(
                    409, "task_not_scheduled", "the task has no complete schedule to pin"
                )
            days = list(current)
    except PinError as exc:
        raise _pin_error(exc) from None
    _set_pins(session, task, days)
    session.commit()
    session.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}/pin", responses=NOT_FOUND)
def unpin_task(task_id: int, session: Db) -> TaskOut:
    task = _task(session, task_id)
    task.pins.clear()
    task.pinned = False
    session.commit()
    session.refresh(task)
    return TaskOut.model_validate(task)
