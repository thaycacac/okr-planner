from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errors import ApiError
from app.api.security import SESSION_COOKIE, AuthState
from app.config import Settings
from app.services.plan_jobs import Clock, PlanJobManager


@dataclass
class AppContext:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    jobs: PlanJobManager
    today: Clock
    auth: AuthState
    llm_transport: httpx.AsyncBaseTransport | None = None


def get_context(request: Request) -> AppContext:
    context: AppContext = request.app.state.context
    return context


Ctx = Annotated[AppContext, Depends(get_context)]


def get_db(ctx: Ctx) -> Iterator[Session]:
    with ctx.session_factory() as session:
        yield session


Db = Annotated[Session, Depends(get_db)]


def require_session(request: Request, ctx: Ctx) -> None:
    if not ctx.auth.sessions.is_valid(request.cookies.get(SESSION_COOKIE)):
        raise ApiError(401, "not_authenticated", "Not signed in")
