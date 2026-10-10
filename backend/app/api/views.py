"""ORM rows → API schemas."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    AllocationOut,
    ClarificationAnswerOut,
    ClarificationQuestion,
    FeasibilityOut,
    FeasibilityStatus,
    ObjectiveOut,
    PlanEvent,
    PlanFailure,
    PlanIssue,
    PlanJob,
    PlanLanguage,
    PlanRunDetail,
    PlanRunStatus,
    PlanStepTrace,
    QuarterDetail,
    QuarterSchedule,
    QuarterSummary,
    ScheduleDay,
    ScheduledTaskOut,
    ScheduleWarningOut,
    UnscheduledTaskOut,
)
from app.persistence.models import (
    KeyResult,
    Objective,
    PlanRun,
    Quarter,
    ScheduleRun,
    Task,
)
from app.services.plan_jobs import resume_blocker
from app.services.scheduling import is_stale, period, quarter_tasks


def quarter_summary(session: Session, quarter: Quarter) -> QuarterSummary:
    span = period(quarter)
    kr_ids = (
        select(KeyResult.id).join(KeyResult.objective).where(Objective.quarter_id == quarter.id)
    )
    latest = session.scalars(
        select(PlanRun)
        .where(PlanRun.quarter_id == quarter.id)
        .order_by(PlanRun.created_at.desc(), PlanRun.id.desc())
        .limit(1)
    ).first()
    return QuarterSummary(
        id=quarter.id,
        year=quarter.year,
        number=quarter.number,
        start_date=span.start,
        end_date=span.end,
        plan_start=quarter.plan_start,
        objective_count=session.scalar(
            select(func.count(Objective.id)).where(Objective.quarter_id == quarter.id)
        )
        or 0,
        key_result_count=session.scalar(select(func.count()).select_from(kr_ids.subquery())) or 0,
        task_count=session.scalar(select(func.count(Task.id)).where(Task.key_result_id.in_(kr_ids)))
        or 0,
        latest_plan_run_id=latest.id if latest else None,
        latest_plan_status=PlanRunStatus(latest.status) if latest else None,
        created_at=quarter.created_at,
    )


def quarter_detail(session: Session, quarter: Quarter) -> QuarterDetail:
    summary = quarter_summary(session, quarter)
    return QuarterDetail(
        **summary.model_dump(),
        objectives=[ObjectiveOut.model_validate(o) for o in quarter.objectives],
    )


def plan_job(run: PlanRun) -> PlanJob:
    return PlanJob(
        job_id=run.id,
        quarter_id=run.quarter_id,
        parent_id=run.parent_id,
        status=PlanRunStatus(run.status),
        round=run.round,
    )


def plan_run_detail(session: Session, run: PlanRun, progress: PlanEvent | None) -> PlanRunDetail:
    schedule_run_id = session.scalar(
        select(ScheduleRun.id).where(ScheduleRun.plan_run_id == run.id).limit(1)
    )
    return PlanRunDetail(
        id=run.id,
        quarter_id=run.quarter_id,
        parent_id=run.parent_id,
        status=PlanRunStatus(run.status),
        round=run.round,
        skip_clarification=run.skip_clarification,
        language=PlanLanguage(run.language) if run.language else None,
        provider=run.provider,
        models=run.models,
        total_retries=run.total_retries,
        stage_duration_ms=run.stage_duration_ms,
        duration_ms=run.duration_ms,
        steps=[PlanStepTrace.model_validate(s) for s in run.steps],
        questions=[ClarificationQuestion.model_validate(q) for q in run.questions],
        clarifications=[ClarificationAnswerOut.model_validate(c) for c in run.clarifications],
        issues=[PlanIssue.model_validate(i) for i in run.issues],
        error=PlanFailure.model_validate(run.error) if run.error else None,
        resumable=run.status == PlanRunStatus.failed.value and resume_blocker(session, run) is None,
        task_count=run.task_count,
        schedule_run_id=schedule_run_id,
        progress=progress,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


def feasibility_out(
    status: str,
    demand_minutes: int,
    supply_minutes: int,
    buffered_supply_minutes: int,
    buffer_start: date | None,
    late: list[UnscheduledTaskOut],
) -> FeasibilityOut:
    return FeasibilityOut(
        status=FeasibilityStatus(status),
        demand_minutes=demand_minutes,
        supply_minutes=supply_minutes,
        buffered_supply_minutes=buffered_supply_minutes,
        buffer_start=buffer_start,
        late_task_ids=sorted(u.task_id for u in late),
        late_key_result_ids=sorted({u.key_result_id for u in late}),
        late_objective_ids=sorted({u.objective_id for u in late}),
    )


def quarter_schedule(session: Session, run: ScheduleRun, today: date) -> QuarterSchedule:
    owners = {
        t.id: (t.key_result_id, t.key_result.objective_id)
        for t in quarter_tasks(session, run.quarter_id)
    }
    by_task: dict[int, list[AllocationOut]] = {}
    flags: dict[int, tuple[bool, bool, bool]] = {}
    for allocation in run.allocations:
        by_task.setdefault(allocation.task_id, []).append(
            AllocationOut(date=allocation.date, minutes=allocation.minutes)
        )
        flags[allocation.task_id] = (allocation.pinned, allocation.uses_buffer, allocation.done)

    scheduled = [
        ScheduledTaskOut(
            task_id=task_id,
            key_result_id=owners[task_id][0],
            objective_id=owners[task_id][1],
            start_date=allocations[0].date,
            end_date=allocations[-1].date,
            allocations=allocations,
            pinned=flags[task_id][0],
            uses_buffer=flags[task_id][1],
            done=flags[task_id][2],
        )
        for task_id, allocations in by_task.items()
        if task_id in owners
    ]
    scheduled.sort(key=lambda s: (s.start_date, s.end_date, s.task_id))
    unscheduled = [
        UnscheduledTaskOut(
            task_id=u["task_id"],
            key_result_id=owners[u["task_id"]][0],
            objective_id=owners[u["task_id"]][1],
            reason=u["reason"],
        )
        for u in run.unscheduled
        if u["task_id"] in owners
    ]
    return QuarterSchedule(
        id=run.id,
        quarter_id=run.quarter_id,
        plan_run_id=run.plan_run_id,
        created_at=run.created_at,
        today=run.today,
        window_start=run.window_start,
        window_end=run.window_end,
        feasibility=feasibility_out(
            run.status,
            run.demand_minutes,
            run.supply_minutes,
            run.buffered_supply_minutes,
            run.buffer_start,
            unscheduled,
        ),
        tasks=scheduled,
        unscheduled=unscheduled,
        warnings=[ScheduleWarningOut.model_validate(w) for w in run.warnings],
        days=[ScheduleDay.model_validate(d) for d in run.days],
        stale=is_stale(session, run, today),
    )
