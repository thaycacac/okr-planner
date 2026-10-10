"""Rescheduling without the LLM and the expected KR milestones of a quarter."""

from datetime import date
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from app.api.deps import Ctx, Db
from app.api.errors import ApiError, error_responses, not_found
from app.api.plans import active_run_exists, plan_in_progress
from app.api.schemas import (
    KeyResultKind,
    KeyResultMilestones,
    MilestoneCheckpoint,
    RescheduleRequest,
    RescheduleResult,
)
from app.api.views import quarter_schedule
from app.persistence.models import Quarter, Task
from app.scheduler import Allocation as ScheduledDay
from app.scheduler import Checkpoint, MilestoneTask, ScheduleInputError, kr_milestones
from app.services.reschedule import reschedule
from app.services.scheduling import latest_schedule, period, quarter_tasks

router = APIRouter(tags=["schedule"])


@router.post("/quarters/{quarter_id}/reschedule", responses=error_responses(404, 409, 422))
def reschedule_quarter(
    quarter_id: int, body: RescheduleRequest, session: Db, ctx: Ctx
) -> RescheduleResult:
    """Recomputes the whole quarter from today with the deterministic scheduler.

    Pinned tasks keep their days. Every pin conflict (overfull day, day off, past day,
    unfinished dependency) is listed; the schedule is stored only when each conflicting task has
    a resolution in the request. Finished tasks keep their history.
    """
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    if active_run_exists(session, quarter_id):
        raise plan_in_progress(quarter_id)
    today = ctx.today()
    resolutions = {r.task_id: r.action for r in body.resolutions}
    try:
        outcome = reschedule(session, quarter, today, resolutions, dry_run=body.dry_run)
    except ScheduleInputError as exc:
        session.rollback()
        raise ApiError(422, "schedule_input_error", str(exc)) from None
    return RescheduleResult(
        applied=outcome.applied,
        conflicts=outcome.conflicts,
        unresolved_task_ids=outcome.unresolved_task_ids,
        changes=outcome.changes,
        before=outcome.before,
        after=outcome.after,
        before_finish_date=outcome.before_finish_date,
        after_finish_date=outcome.after_finish_date,
        schedule=quarter_schedule(session, outcome.run, today) if outcome.run else None,
    )


def _checkpoint(c: Checkpoint) -> MilestoneCheckpoint:
    return MilestoneCheckpoint(
        period_end=c.period_end,
        completed_minutes=c.completed_minutes,
        progress=c.progress,
        expected_value=c.expected_value,
    )


@router.get("/quarters/{quarter_id}/kr-milestones", responses=error_responses(404))
def get_kr_milestones(quarter_id: int, session: Db, ctx: Ctx) -> list[KeyResultMilestones]:
    """Weekly and monthly expected values of each active KR of an active objective.

    ``expected_value`` is null for KRs without a numeric baseline and target. Without a stored
    schedule only finished tasks count.
    """
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    span = period(quarter)
    zone = ZoneInfo(ctx.settings.app_timezone)
    run = latest_schedule(session, quarter_id)
    scheduled: dict[int, list[ScheduledDay]] = {}
    for a in run.allocations if run else []:
        if not a.done:
            scheduled.setdefault(a.task_id, []).append(ScheduledDay(date=a.date, minutes=a.minutes))

    def done_on(task: Task) -> date:
        if task.completed_at is None:
            return span.start
        return task.completed_at.astimezone(zone).date()

    by_kr: dict[int, list[MilestoneTask]] = {}
    for task in quarter_tasks(session, quarter_id):
        by_kr.setdefault(task.key_result_id, []).append(
            MilestoneTask(
                estimate_minutes=task.estimate_minutes,
                done_on=done_on(task) if task.status == "done" else None,
                allocations=tuple(scheduled.get(task.id, ())),
            )
        )

    result = []
    for objective in sorted(quarter.objectives, key=lambda o: (o.position, o.id)):
        if not objective.active:
            continue
        for kr in sorted(objective.key_results, key=lambda k: (k.position, k.id)):
            if not kr.active:
                continue
            milestones = kr_milestones(span, tuple(by_kr.get(kr.id, ())), kr.baseline, kr.target)
            result.append(
                KeyResultMilestones(
                    key_result_id=kr.id,
                    objective_id=objective.id,
                    kind=KeyResultKind(kr.kind),
                    baseline=kr.baseline,
                    target=kr.target,
                    unit=kr.unit,
                    total_minutes=milestones.total_minutes,
                    planned_minutes=milestones.planned_minutes,
                    expected_completion_date=milestones.expected_completion,
                    weekly=[_checkpoint(c) for c in milestones.weekly],
                    monthly=[_checkpoint(c) for c in milestones.monthly],
                )
            )
    return result
