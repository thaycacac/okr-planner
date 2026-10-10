import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import sessionmaker
from starlette.concurrency import run_in_threadpool

from app.api.auth import router as auth_router
from app.api.calendar import router as calendar_router
from app.api.deps import AppContext, require_session
from app.api.errors import error_responses
from app.api.export import router as export_router
from app.api.health import router as health_router
from app.api.http_security import install_http_security
from app.api.okr import router as okr_router
from app.api.options import router as options_router
from app.api.plans import router as plans_router
from app.api.schedule import router as schedule_router
from app.api.security import AuthState, check_auth_settings
from app.api.settings import router as settings_router
from app.api.tasks import router as tasks_router
from app.config import Settings, get_settings
from app.persistence.db import create_db_engine
from app.planner_llm import LLMProvider
from app.planner_llm.providers import select_provider
from app.services.plan_jobs import Clock, PlanJobManager, ProviderResolver

logger = logging.getLogger(__name__)


async def default_provider_resolver(settings: Settings) -> LLMProvider:
    return await select_provider(settings)


def default_clock(settings: Settings) -> Clock:
    zone = ZoneInfo(settings.app_timezone)

    def today() -> date:
        return datetime.now(zone).date()

    return today


def create_app(
    settings: Settings | None = None,
    *,
    engine: Engine | None = None,
    provider_resolver: ProviderResolver | None = None,
    today: Clock | None = None,
    llm_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    check_auth_settings(settings)
    engine = engine or create_db_engine(settings.database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    jobs = PlanJobManager(
        session_factory,
        settings,
        provider_resolver or default_provider_resolver,
        today or default_clock(settings),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if await run_in_threadpool(lambda: inspect(engine).has_table("plan_runs")):
            interrupted = await run_in_threadpool(jobs.mark_interrupted)
            if interrupted:
                logger.warning("marked %d unfinished plan runs as interrupted", interrupted)
        yield
        await jobs.shutdown()

    # The Next.js proxy exposes every backend path under /api, so prod does not publish the
    # schema or the interactive docs.
    public_docs = settings.app_env != "prod"
    app = FastAPI(
        title="OKR Planner API",
        version="0.1.0",
        lifespan=lifespan,
        # One schema per model keeps names such as CalendarSettings stable for the frontend.
        separate_input_output_schemas=False,
        openapi_url="/openapi.json" if public_docs else None,
    )
    app.state.context = AppContext(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        jobs=jobs,
        today=jobs.today,
        auth=AuthState.from_settings(settings),
        llm_transport=llm_transport,
    )
    install_http_security(app, settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    protected = (
        okr_router,
        tasks_router,
        schedule_router,
        options_router,
        export_router,
        calendar_router,
        plans_router,
        settings_router,
    )
    for router in protected:
        app.include_router(
            router, dependencies=[Depends(require_session)], responses=error_responses(401)
        )
    return app


app = create_app()
