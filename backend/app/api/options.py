"""Overload options (what-if): every number comes from a real scheduler run, never the LLM."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Header
from sqlalchemy.orm import Session

from app.api.deps import Ctx, Db
from app.api.errors import ApiError, error_responses, not_found
from app.api.plans import active_run_exists, plan_in_progress
from app.api.schemas import (
    OptionApplication,
    OptionEffect,
    OptionEvaluation,
    OptionOutcome,
    OptionSelection,
    OverloadOptions,
)
from app.api.views import quarter_schedule
from app.persistence.models import OptionApplication as OptionApplicationRow
from app.persistence.models import Quarter
from app.scheduler import ScheduleInputError
from app.scheduler.whatif import OptionError
from app.services import whatif
from app.services.scheduling import latest_schedule

router = APIRouter(tags=["options"])
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=200,
        description="Repeating a request with the same key returns the first result",
    ),
]


def _quarter(session: Session, quarter_id: int) -> Quarter:
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    return quarter


def _error(session: Session, exc: Exception) -> ApiError:
    session.rollback()
    if isinstance(exc, whatif.StateConflict):
        return ApiError(409, exc.code, str(exc))
    if isinstance(exc, OptionError):
        return ApiError(422, exc.code, str(exc))
    return ApiError(422, "schedule_input_error", str(exc))


def _application(session: Session, row: OptionApplicationRow, today: date) -> OptionApplication:
    run = latest_schedule(session, row.quarter_id)
    assert run is not None, "applying or undoing options always stores a schedule"
    return OptionApplication(
        id=row.id,
        quarter_id=row.quarter_id,
        option_ids=row.option_ids,
        before=OptionOutcome.model_validate(row.before),
        after=OptionOutcome.model_validate(row.after),
        effects=[OptionEffect.model_validate(e) for e in row.effects],
        created_at=row.created_at,
        undone_at=row.undone_at,
        schedule=quarter_schedule(session, run, today),
    )


@router.get("/quarters/{quarter_id}/options", responses=error_responses(404, 422))
def list_options(quarter_id: int, session: Db, ctx: Ctx) -> OverloadOptions:
    """Each option on its own (more hours on weekdays, Saturdays, Sundays, holidays, drop the
    lowest-priority late KR or objective, defer each late KR to the next quarter).

    ``weekday_hint`` gives the smallest extra minutes per weekday that clears the red warnings
    and that turns the plan green. Nothing is stored; no option is selected by default.
    """
    quarter = _quarter(session, quarter_id)
    try:
        result = whatif.list_options(session, quarter, ctx.today())
    except ScheduleInputError as exc:
        raise _error(session, exc) from None
    session.rollback()
    return result


@router.post("/quarters/{quarter_id}/options/evaluate", responses=error_responses(404, 422))
def evaluate_options(
    quarter_id: int, body: OptionSelection, session: Db, ctx: Ctx
) -> OptionEvaluation:
    """Before/after of a combination of options, from one scheduler run; nothing is stored.

    422 ``options_conflict`` when two options exclude each other (e.g. dropping and deferring
    the same KR), ``unknown_option`` or ``option_not_applicable`` for invalid ids.
    """
    quarter = _quarter(session, quarter_id)
    try:
        result = whatif.evaluate(session, quarter, ctx.today(), body.option_ids)
    except (OptionError, ScheduleInputError) as exc:
        raise _error(session, exc) from None
    session.rollback()
    return result


@router.post("/quarters/{quarter_id}/options/apply", responses=error_responses(404, 409, 422))
def apply_options(
    quarter_id: int,
    body: OptionSelection,
    session: Db,
    ctx: Ctx,
    idempotency_key: IdempotencyKey,
) -> OptionApplication:
    """Applies the options and stores a new schedule in one transaction.

    Calendar options change this quarter's own settings, never the global ones. Deferring a KR
    moves it with its tasks to the next quarter (created when missing). The same
    ``Idempotency-Key`` with the same body returns the first result; with another body it is
    409 ``idempotency_key_reused``. 409 ``plan_in_progress`` while a plan is running.
    """
    quarter = _quarter(session, quarter_id)
    if active_run_exists(session, quarter_id):
        raise plan_in_progress(quarter_id)
    today = ctx.today()
    try:
        row = whatif.apply(session, quarter, today, body.option_ids, idempotency_key)
    except (OptionError, ScheduleInputError) as exc:
        raise _error(session, exc) from None
    return _application(session, row, today)


@router.post("/option-applications/{application_id}/undo", responses=error_responses(404, 409, 422))
def undo_options(application_id: int, session: Db, ctx: Ctx) -> OptionApplication:
    """Restores the settings, KRs and objectives changed by the application and reschedules.

    Undoing twice returns the same result. 409 ``undo_not_latest`` when a later application of
    the quarter is still in place, ``undo_conflict`` when a moved KR has nowhere to go back to.
    """
    row = session.get(OptionApplicationRow, application_id)
    if row is None:
        raise not_found("option application", application_id)
    if row.undone_at is None and active_run_exists(session, row.quarter_id):
        raise plan_in_progress(row.quarter_id)
    today = ctx.today()
    try:
        row = whatif.undo(session, row, today)
    except (OptionError, ScheduleInputError) as exc:
        raise _error(session, exc) from None
    return _application(session, row, today)
