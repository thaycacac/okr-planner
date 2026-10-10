"""Plan jobs: create, follow progress over SSE, answer clarification questions, resume a
failed run, cancel."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import AppContext, Ctx
from app.api.errors import ApiError, error_responses, not_found
from app.api.schemas import (
    PlanAnswers,
    PlanCreate,
    PlanEvent,
    PlanEventType,
    PlanJob,
    PlanRunDetail,
    PlanRunStatus,
)
from app.api.views import plan_job, plan_run_detail
from app.persistence.models import PlanRun, Quarter
from app.services.plan_jobs import (
    ACTIVE_STATUSES,
    MAX_CLARIFY_ROUNDS,
    new_run_id,
    resume_blocker,
)

router = APIRouter(tags=["plans"])


def active_run_exists(session: Session, quarter_id: int) -> bool:
    return (
        session.scalar(
            select(PlanRun.id)
            .where(PlanRun.quarter_id == quarter_id, PlanRun.status.in_(ACTIVE_STATUSES))
            .limit(1)
        )
        is not None
    )


def plan_in_progress(quarter_id: int) -> ApiError:
    return ApiError(409, "plan_in_progress", f"a plan is already running for quarter {quarter_id}")


def _create_run(ctx: AppContext, body: PlanCreate) -> PlanJob:
    with ctx.session_factory() as session:
        if session.get(Quarter, body.quarter_id) is None:
            raise not_found("quarter", body.quarter_id)
        if active_run_exists(session, body.quarter_id):
            raise plan_in_progress(body.quarter_id)
        run = PlanRun(
            id=new_run_id(),
            quarter_id=body.quarter_id,
            status=PlanRunStatus.queued.value,
            round=1,
            skip_clarification=body.skip_clarification,
            context=body.context,
            language=body.language.value if body.language else None,
            clarifications=[],
        )
        session.add(run)
        session.commit()
        return plan_job(run)


def _create_answer_run(ctx: AppContext, parent_id: str, body: PlanAnswers) -> PlanJob:
    with ctx.session_factory() as session:
        parent = session.get(PlanRun, parent_id)
        if parent is None:
            raise not_found("plan", parent_id)
        if parent.status != PlanRunStatus.needs_clarification.value:
            raise ApiError(409, "plan_not_awaiting_answers", f"plan {parent_id} is {parent.status}")
        child = session.scalar(select(PlanRun.id).where(PlanRun.parent_id == parent.id).limit(1))
        if child is not None:
            raise ApiError(409, "plan_already_answered", f"plan {parent_id} continued as {child}")
        if active_run_exists(session, parent.quarter_id):
            raise plan_in_progress(parent.quarter_id)
        questions = {q["id"]: q for q in parent.questions}
        unknown = sorted({a.question_id for a in body.answers} - questions.keys())
        if unknown:
            raise ApiError(422, "unknown_question", f"unknown question ids: {', '.join(unknown)}")
        answers = [
            {
                "question_id": a.question_id,
                "key_result_id": questions[a.question_id]["key_result_id"],
                "question": questions[a.question_id]["question"],
                "answer": a.answer.strip(),
            }
            for a in body.answers
        ]
        run = PlanRun(
            id=new_run_id(),
            quarter_id=parent.quarter_id,
            parent_id=parent.id,
            status=PlanRunStatus.queued.value,
            round=parent.round + 1,
            skip_clarification=body.generate_anyway or parent.round >= MAX_CLARIFY_ROUNDS,
            context=parent.context,
            language=parent.language,
            clarifications=[*parent.clarifications, *answers],
        )
        session.add(run)
        session.commit()
        return plan_job(run)


def _create_resume_run(ctx: AppContext, failed_id: str) -> PlanJob:
    with ctx.session_factory() as session:
        failed = session.get(PlanRun, failed_id)
        if failed is None:
            raise not_found("plan", failed_id)
        if active_run_exists(session, failed.quarter_id):
            raise plan_in_progress(failed.quarter_id)
        blocker = resume_blocker(session, failed)
        if blocker is not None:
            raise ApiError(409, *blocker)
        # Failing at decompose or dedup means clarification already passed.
        run = PlanRun(
            id=new_run_id(),
            quarter_id=failed.quarter_id,
            parent_id=failed.id,
            status=PlanRunStatus.queued.value,
            round=failed.round,
            skip_clarification=True,
            context=failed.context,
            language=failed.language,
            clarifications=list(failed.clarifications),
        )
        session.add(run)
        session.commit()
        return plan_job(run)


def _load_run(ctx: AppContext, run_id: str) -> PlanRun:
    with ctx.session_factory() as session:
        run = session.get(PlanRun, run_id)
        if run is None:
            raise not_found("plan", run_id)
        return run


def _detail(ctx: AppContext, run_id: str) -> PlanRunDetail:
    with ctx.session_factory() as session:
        run = session.get(PlanRun, run_id)
        if run is None:
            raise not_found("plan", run_id)
        log = ctx.jobs.log(run_id)
        return plan_run_detail(session, run, log.last if log else None)


@router.post("/plans", status_code=status.HTTP_202_ACCEPTED, responses=error_responses(404, 409))
async def create_plan(body: PlanCreate, ctx: Ctx) -> PlanJob:
    """Start generating the quarter's plan; follow it with ``GET /plans/{job_id}/events``."""
    job = await run_in_threadpool(_create_run, ctx, body)
    ctx.jobs.start(job.job_id)
    return job


@router.get("/plans/{job_id}", responses=error_responses(404))
async def get_plan(job_id: str, ctx: Ctx) -> PlanRunDetail:
    """Outcome and trace of a run; also the polling fallback for SSE (see ``progress``)."""
    return await run_in_threadpool(_detail, ctx, job_id)


@router.post(
    "/plans/{job_id}/answers",
    status_code=status.HTTP_202_ACCEPTED,
    responses=error_responses(404, 409, 422),
)
async def answer_plan(job_id: str, body: PlanAnswers, ctx: Ctx) -> PlanJob:
    """Answer the clarification questions of a run; starts a new run (new ``job_id``)."""
    job = await run_in_threadpool(_create_answer_run, ctx, job_id, body)
    ctx.jobs.start(job.job_id)
    return job


@router.post(
    "/plans/{job_id}/resume",
    status_code=status.HTTP_202_ACCEPTED,
    responses=error_responses(404, 409),
)
async def resume_plan(job_id: str, ctx: Ctx) -> PlanJob:
    """Continue a run that failed at ``decompose`` or ``dedup``; starts a new run (new
    ``job_id``, ``parent_id`` = the failed run) that only asks the model for the key results
    not yet decomposed. 409 ``okr_changed`` when the OKR was edited since: generate anew."""
    job = await run_in_threadpool(_create_resume_run, ctx, job_id)
    ctx.jobs.start(job.job_id)
    return job


@router.post(
    "/plans/{job_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    responses=error_responses(404, 409),
)
async def cancel_plan(job_id: str, ctx: Ctx) -> PlanJob:
    run = await run_in_threadpool(_load_run, ctx, job_id)
    if not await ctx.jobs.cancel(job_id):
        raise ApiError(409, "plan_not_running", f"plan {job_id} is {run.status}")
    return plan_job(await run_in_threadpool(_load_run, ctx, job_id))


def _sse(event: PlanEvent) -> str:
    return f"id: {event.seq}\nevent: {event.type.value}\ndata: {event.model_dump_json()}\n\n"


@router.get(
    "/plans/{job_id}/events",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Server-sent events; each `data` is a `PlanEvent`, the last has "
            "`type: end`. Reconnect with `Last-Event-ID` to resume.",
            "content": {
                "text/event-stream": {"schema": {"$ref": "#/components/schemas/PlanEvent"}}
            },
        },
        **error_responses(404),
    },
)
async def plan_events(
    job_id: str,
    ctx: Ctx,
    last_event_id: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    run = await run_in_threadpool(_load_run, ctx, job_id)
    after = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    log = ctx.jobs.log(job_id)

    async def stream() -> AsyncIterator[str]:
        if log is None:
            # Finished before this process kept its progress (restart or evicted log).
            yield _sse(
                PlanEvent(
                    seq=after + 1,
                    type=PlanEventType.end,
                    run_status=PlanRunStatus(run.status),
                    stage=None,
                    status=None,
                    objective_id=None,
                    key_result_id=None,
                    attempt=None,
                    completed=None,
                    total=None,
                    duration_ms=None,
                    percent=100 if run.status == PlanRunStatus.succeeded.value else 0,
                )
            )
            return
        async for event in log.follow(after):
            yield ": keep-alive\n\n" if event is None else _sse(event)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        # no-transform stops proxy compression (Next.js rewrites) from buffering the stream.
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
