"""Quarters, objectives and key results (read/write); task editing lives in ``tasks.py``."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.api.deps import AppContext, Ctx, Db
from app.api.errors import ApiError, error_responses, not_found
from app.api.plans import active_run_exists, plan_in_progress
from app.api.schemas import (
    KeyResultCreate,
    KeyResultOut,
    KeyResultUpdate,
    ObjectiveCreate,
    ObjectiveOut,
    ObjectiveUpdate,
    OkrParseObjective,
    OkrParseRequest,
    OkrParseResult,
    QuarterCreate,
    QuarterDetail,
    QuarterPlanStartUpdate,
    QuarterSchedule,
    QuarterSummary,
    TaskOut,
)
from app.api.views import quarter_detail, quarter_schedule, quarter_summary
from app.config import Settings
from app.domain.quarter import Quarter as QuarterSpan
from app.persistence.models import KeyResult, Objective, Quarter
from app.planner_llm.okr_parse import ParsedOkr, normalize, okr_parse_prompt
from app.planner_llm.pipeline import provider_semaphore
from app.planner_llm.providers import InvalidJSONError, Prompt, ProviderError
from app.services import llm_settings
from app.services.scheduling import latest_schedule, period, quarter_tasks

router = APIRouter()
NOT_FOUND = error_responses(404)


def _quarter(session: Session, quarter_id: int) -> Quarter:
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    return quarter


def _objective(session: Session, objective_id: int) -> Objective:
    objective = session.get(Objective, objective_id)
    if objective is None:
        raise not_found("objective", objective_id)
    return objective


def _key_result(session: Session, kr_id: int) -> KeyResult:
    kr = session.get(KeyResult, kr_id)
    if kr is None:
        raise not_found("key result", kr_id)
    return kr


def _next_position(
    session: Session, column: InstrumentedAttribute[int], parent_filter: ColumnElement[bool]
) -> int:
    current = session.scalar(select(func.max(column)).where(parent_filter))
    return 0 if current is None else int(current) + 1


def _new_key_result(body: KeyResultCreate, position: int) -> KeyResult:
    return KeyResult(
        text=body.text.strip(),
        kind=body.kind.value,
        baseline=body.baseline,
        target=body.target,
        unit=body.unit,
        due_date=body.due_date,
        note=body.note,
        position=body.position if body.position is not None else position,
    )


# --- free-text OKR input ----------------------------------------------------------------------


def _effective_settings(ctx: AppContext) -> Settings:
    with ctx.session_factory() as session:
        return llm_settings.effective_settings(session, ctx.settings)


@router.post(
    "/okr/parse",
    tags=["okr"],
    summary="Structure free-text OKRs with the selected AI provider",
    responses=error_responses(422, 502),
)
async def parse_okr_text(body: OkrParseRequest, ctx: Ctx) -> OkrParseResult:
    """Splits the text into Objectives and Key Results and guesses each KR's kind, target, unit
    and due date. Nothing is stored; the client adds the result to its draft."""
    span = QuarterSpan(year=body.year, number=body.number)
    system, user = okr_parse_prompt(body.text, span.start, span.end)
    settings = await run_in_threadpool(_effective_settings, ctx)
    provider = await ctx.jobs.provider_resolver(settings)
    parsed: ParsedOkr | None = None
    for attempt in range(2):
        try:
            async with provider_semaphore(provider):
                raw = await provider.generate_json(
                    Prompt(step="decompose", system=system, user=user, attempt=attempt),
                    ParsedOkr,
                )
            parsed = ParsedOkr.model_validate(raw)
            break
        except (InvalidJSONError, ValidationError):
            continue
        except ProviderError as exc:
            raise ApiError(502, "llm_unavailable", str(exc) or type(exc).__name__) from exc
    if parsed is None:
        raise ApiError(502, "llm_invalid_output", "The AI returned an unusable answer")
    cleaned = normalize(parsed, span.start, span.end)
    return OkrParseResult(
        objectives=[OkrParseObjective.model_validate(o.model_dump()) for o in cleaned.objectives]
    )


# --- quarters -------------------------------------------------------------------------------


@router.get("/quarters", tags=["quarters"])
def list_quarters(
    session: Db,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    number: Annotated[int | None, Query(ge=1, le=4)] = None,
) -> list[QuarterSummary]:
    query = select(Quarter).order_by(Quarter.year, Quarter.number)
    if year is not None:
        query = query.where(Quarter.year == year)
    if number is not None:
        query = query.where(Quarter.number == number)
    return [quarter_summary(session, q) for q in session.scalars(query).all()]


@router.post(
    "/quarters",
    tags=["quarters"],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
def create_quarter(body: QuarterCreate, session: Db) -> QuarterDetail:
    quarter = Quarter(year=body.year, number=body.number)
    session.add(quarter)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(
            409, "quarter_exists", f"Q{body.number}/{body.year} already exists"
        ) from None
    return quarter_detail(session, quarter)


@router.get("/quarters/{quarter_id}", tags=["quarters"], responses=NOT_FOUND)
def get_quarter(quarter_id: int, session: Db) -> QuarterDetail:
    return quarter_detail(session, _quarter(session, quarter_id))


@router.put(
    "/quarters/{quarter_id}/plan-start",
    tags=["quarters"],
    responses=error_responses(404, 409, 422),
)
def set_plan_start(quarter_id: int, body: QuarterPlanStartUpdate, session: Db) -> QuarterDetail:
    """Sets the first day tasks may be scheduled (e.g. Q4 but start on 10 Oct). Existing
    schedules are not recomputed; they show as stale until the next plan or reschedule."""
    quarter = _quarter(session, quarter_id)
    if active_run_exists(session, quarter_id):
        raise plan_in_progress(quarter_id)
    span = period(quarter)
    if body.plan_start is not None and not span.start <= body.plan_start <= span.end:
        raise ApiError(
            422,
            "plan_start_outside_quarter",
            f"plan_start must be between {span.start} and {span.end}",
        )
    quarter.plan_start = body.plan_start
    session.commit()
    return quarter_detail(session, quarter)


@router.get("/quarters/{quarter_id}/previous", tags=["quarters"], responses=NOT_FOUND)
def get_previous_quarter(quarter_id: int, session: Db) -> QuarterDetail:
    """The closest earlier quarter that exists; 404 ``no_previous_quarter`` when there is none."""
    quarter = _quarter(session, quarter_id)
    previous = session.scalars(
        select(Quarter)
        .where(
            (Quarter.year < quarter.year)
            | ((Quarter.year == quarter.year) & (Quarter.number < quarter.number))
        )
        .order_by(Quarter.year.desc(), Quarter.number.desc())
        .limit(1)
    ).first()
    if previous is None:
        raise ApiError(404, "no_previous_quarter", f"no quarter before quarter {quarter_id}")
    return quarter_detail(session, previous)


@router.delete(
    "/quarters/{quarter_id}",
    tags=["quarters"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404, 409),
)
def delete_quarter(quarter_id: int, session: Db) -> Response:
    """Deletes the quarter's data: OKRs, tasks, pins, plan and schedule runs, calendar override.

    Global data (leave days, holidays, settings) is kept. 409 while a plan is running.
    """
    quarter = _quarter(session, quarter_id)
    if active_run_exists(session, quarter_id):
        raise plan_in_progress(quarter_id)
    session.delete(quarter)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/quarters/{quarter_id}/tasks", tags=["tasks"], responses=NOT_FOUND)
def list_quarter_tasks(quarter_id: int, session: Db) -> list[TaskOut]:
    _quarter(session, quarter_id)
    return [TaskOut.model_validate(t) for t in quarter_tasks(session, quarter_id)]


@router.get("/quarters/{quarter_id}/schedule", tags=["schedule"], responses=NOT_FOUND)
def get_quarter_schedule(quarter_id: int, session: Db, ctx: Ctx) -> QuarterSchedule:
    """Latest schedule of the quarter; 404 ``schedule_not_found`` until a plan succeeded
    or the quarter was rescheduled."""
    _quarter(session, quarter_id)
    run = latest_schedule(session, quarter_id)
    if run is None:
        raise ApiError(404, "schedule_not_found", f"quarter {quarter_id} has no schedule yet")
    return quarter_schedule(session, run, ctx.today())


# --- objectives -----------------------------------------------------------------------------


@router.post(
    "/quarters/{quarter_id}/objectives",
    tags=["objectives"],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_objective(quarter_id: int, body: ObjectiveCreate, session: Db) -> ObjectiveOut:
    _quarter(session, quarter_id)
    position = body.position
    if position is None:
        position = _next_position(session, Objective.position, Objective.quarter_id == quarter_id)
    objective = Objective(
        quarter_id=quarter_id,
        title=body.title.strip(),
        priority=body.priority.value,
        position=position,
        active=body.active,
        key_results=[_new_key_result(kr, i) for i, kr in enumerate(body.key_results)],
    )
    session.add(objective)
    session.commit()
    return ObjectiveOut.model_validate(objective)


@router.get("/objectives/{objective_id}", tags=["objectives"], responses=NOT_FOUND)
def get_objective(objective_id: int, session: Db) -> ObjectiveOut:
    return ObjectiveOut.model_validate(_objective(session, objective_id))


@router.patch("/objectives/{objective_id}", tags=["objectives"], responses=NOT_FOUND)
def update_objective(objective_id: int, body: ObjectiveUpdate, session: Db) -> ObjectiveOut:
    objective = _objective(session, objective_id)
    changes = body.model_dump(exclude_unset=True)
    for field in ("title", "priority", "position", "active"):
        if changes.get(field) is not None:
            value = changes[field]
            setattr(objective, field, value.strip() if field == "title" else value)
    session.commit()
    return ObjectiveOut.model_validate(objective)


@router.delete(
    "/objectives/{objective_id}",
    tags=["objectives"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_objective(objective_id: int, session: Db) -> Response:
    session.delete(_objective(session, objective_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- key results ----------------------------------------------------------------------------


@router.post(
    "/objectives/{objective_id}/key-results",
    tags=["key-results"],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_key_result(objective_id: int, body: KeyResultCreate, session: Db) -> KeyResultOut:
    objective = _objective(session, objective_id)
    position = _next_position(session, KeyResult.position, KeyResult.objective_id == objective_id)
    kr = _new_key_result(body, position)
    objective.key_results.append(kr)
    session.commit()
    return KeyResultOut.model_validate(kr)


@router.get("/key-results/{kr_id}", tags=["key-results"], responses=NOT_FOUND)
def get_key_result(kr_id: int, session: Db) -> KeyResultOut:
    return KeyResultOut.model_validate(_key_result(session, kr_id))


@router.patch("/key-results/{kr_id}", tags=["key-results"], responses=NOT_FOUND)
def update_key_result(kr_id: int, body: KeyResultUpdate, session: Db) -> KeyResultOut:
    kr = _key_result(session, kr_id)
    changes = body.model_dump(exclude_unset=True)
    for field in ("text", "kind", "position", "active"):
        if field in changes and changes[field] is None:
            raise ApiError(422, "field_required", f"{field} cannot be null")
    for field, value in changes.items():
        setattr(kr, field, value.strip() if field == "text" else value)
    session.commit()
    return KeyResultOut.model_validate(kr)


@router.delete(
    "/key-results/{kr_id}",
    tags=["key-results"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_key_result(kr_id: int, session: Db) -> Response:
    session.delete(_key_result(session, kr_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
