"""Collect a quarter's tasks and its latest stored schedule into ``ExportData``."""

from datetime import date

from sqlalchemy.orm import Session

from app.exporters import DayRow, ExportData, Language, TaskRow
from app.persistence.models import Quarter
from app.services.scheduling import latest_schedule, quarter_tasks


def export_data(
    session: Session, quarter: Quarter, language: Language, *, details: bool = False
) -> ExportData:
    """Hours come from the latest ``ScheduleRun``; without one, tasks are listed unscheduled.

    The task sheet includes the history days of finished tasks; the daily and weekly sheets
    cover the schedule window, where only unfinished work takes capacity.
    """
    objectives = sorted(quarter.objectives, key=lambda o: (o.position, o.id))
    objective_index = {o.id: i for i, o in enumerate(objectives)}
    tasks = sorted(
        quarter_tasks(session, quarter.id),
        key=lambda t: (
            objective_index[t.key_result.objective_id],
            t.key_result.position,
            t.key_result_id,
            t.position,
            t.id,
        ),
    )
    run = latest_schedule(session, quarter.id)
    allocations = list(run.allocations) if run else []
    late = {u["task_id"]: u["reason"] for u in run.unscheduled} if run else {}

    by_task: dict[int, list[tuple[date, int, bool]]] = {}
    for a in allocations:
        by_task.setdefault(a.task_id, []).append((a.date, a.minutes, a.uses_buffer))
    task_rows = []
    for task in tasks:
        days = sorted(by_task.get(task.id, []))
        task_rows.append(
            TaskRow(
                task_id=task.id,
                objective=task.key_result.objective.title,
                key_result=task.key_result.text,
                title=task.title,
                estimate_minutes=task.estimate_minutes,
                status=task.status,
                pinned=task.pinned,
                start=days[0][0] if days else None,
                end=days[-1][0] if days else None,
                scheduled_minutes=sum(m for _, m, _ in days),
                uses_buffer=any(b for _, _, b in days),
                late_reason=late.get(task.id),
                done_criteria=task.done_criteria,
                depends_on=tuple(task.depends_on),
            )
        )

    titles = {t.id: t.title for t in tasks}
    objective_of = {t.id: objective_index[t.key_result.objective_id] for t in tasks}
    per_day: dict[date, list[tuple[str, int]]] = {}
    per_day_objective: dict[date, list[int]] = {}
    for a in allocations:
        if a.done or a.task_id not in titles:
            continue
        per_day.setdefault(a.date, []).append((titles[a.task_id], a.minutes))
        split = per_day_objective.setdefault(a.date, [0] * len(objectives))
        split[objective_of[a.task_id]] += a.minutes
    day_rows = []
    for day in run.days if run else []:
        on = date.fromisoformat(day["date"])
        day_rows.append(
            DayRow(
                date=on,
                capacity_minutes=day["capacity_minutes"],
                scheduled_minutes=day["scheduled_minutes"],
                is_buffer=day["is_buffer"],
                off_reason=day["off_reason"],
                tasks=tuple(per_day.get(on, ())),
                objective_minutes=tuple(per_day_objective.get(on, [0] * len(objectives))),
            )
        )
    return ExportData(
        quarter_label=f"Q{quarter.number}/{quarter.year}",
        language=language,
        objectives=tuple(o.title for o in objectives),
        tasks=tuple(task_rows),
        days=tuple(day_rows),
        details=details,
    )
