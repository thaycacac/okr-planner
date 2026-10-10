from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import Ctx

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(ctx: Ctx) -> dict[str, str]:
    with ctx.engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
