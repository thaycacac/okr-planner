from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.api.deps import AppContext, Ctx, Db
from app.api.schemas import (
    CalendarSettings,
    LlmSettings,
    LlmSettingsUpdate,
    LlmTestRequest,
    LlmTestResult,
    WeekdayCapacity,
)
from app.config import Settings
from app.persistence.models import CalendarSettings as CalendarSettingsRow
from app.services import llm_settings
from app.services.scheduling import WEEKDAY_COLUMNS, global_calendar, weekday_minutes

router = APIRouter(prefix="/settings", tags=["settings"])


def calendar_schema(row: CalendarSettingsRow) -> CalendarSettings:
    minutes = dict(zip(WEEKDAY_COLUMNS, weekday_minutes(row), strict=True))
    return CalendarSettings(
        capacity_minutes=WeekdayCapacity(**minutes),
        work_saturday=row.work_saturday,
        work_sunday=row.work_sunday,
        work_holidays=row.work_holidays,
    )


@router.get("/calendar", summary="Global work calendar settings")
def get_calendar_settings(session: Db) -> CalendarSettings:
    row = global_calendar(session)
    session.commit()
    return calendar_schema(row)


@router.put("/calendar", summary="Replace global work calendar settings")
def put_calendar_settings(body: CalendarSettings, session: Db) -> CalendarSettings:
    """Existing schedules are not recomputed; the next plan run uses the new values."""
    row = global_calendar(session)
    for day in WEEKDAY_COLUMNS:
        setattr(row, f"{day}_minutes", getattr(body.capacity_minutes, day))
    row.work_saturday = body.work_saturday
    row.work_sunday = body.work_sunday
    row.work_holidays = body.work_holidays
    session.commit()
    return calendar_schema(row)


@router.get("/llm", summary="LLM provider settings")
def get_llm_settings(session: Db, ctx: Ctx) -> LlmSettings:
    return llm_settings.read(session, ctx.settings)


@router.put("/llm", summary="Update LLM provider settings")
def put_llm_settings(body: LlmSettingsUpdate, session: Db, ctx: Ctx) -> LlmSettings:
    return llm_settings.update(session, ctx.settings, body)


def _effective(ctx: AppContext) -> Settings:
    with ctx.session_factory() as session:
        return llm_settings.effective_settings(session, ctx.settings)


@router.post("/llm/test", summary="Send one small structured prompt to the selected provider")
async def test_llm(body: LlmTestRequest, ctx: Ctx) -> LlmTestResult:
    """Always 200: a failed probe is reported in ``ok``/``error_code``, not as an HTTP error."""
    settings = await run_in_threadpool(_effective, ctx)
    return await llm_settings.test_connection(settings, body, ctx.llm_transport)
