"""Backend for the Playwright suite: the real API on a fresh SQLite file, with ``FakeProvider``
in place of an LLM so no network or model is needed.

    cd backend && python -m tests.e2e_server --port 8217 --frontend-origin http://localhost:3217

The first clarify round of every plan asks one question; once the user has answered, clarify
accepts. Each KR is broken into three chained 4-hour tasks.
"""

import argparse
import os
import tempfile
from pathlib import Path
from typing import Any

import uvicorn
from argon2 import PasswordHasher
from pydantic import BaseModel, SecretStr

from app.config import Settings
from app.persistence.db import create_db_engine
from app.planner_llm import LLMProvider
from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.fake import FakeProvider, FakeReply
from app.planner_llm.schemas import KeyResultCheck, KeyResultNeedsOutput

E2E_PASSWORD = "e2e-okr-planner"
CLARIFY_QUESTION = "Bạn dành được bao nhiêu giờ mỗi ngày cho các OKR này?"


def _task(local_id: str, kr_id: str, deps: list[str]) -> dict[str, Any]:
    return {
        "local_id": local_id,
        "title": f"Task {local_id} for {kr_id}",
        "description": "Do the work",
        "estimate_hours": 4,
        "done_criteria": "Reviewed",
        "depends_on": deps,
        "kr_id": kr_id,
    }


def e2e_llm(prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
    if schema is KeyResultCheck:
        return {"end_result": "", "concrete": '"clarifications"' in prompt.user}
    if schema is KeyResultNeedsOutput:
        return {"needs": []}
    if prompt.step == "clarify":
        return {
            "status": "needs_clarification",
            "questions": [{"kr_id": None, "question": CLARIFY_QUESTION, "reason": "capacity"}],
        }
    if prompt.step == "decompose":
        assert prompt.kr_id is not None
        kr = prompt.kr_id
        return {"tasks": [_task("t1", kr, []), _task("t2", kr, ["t1"]), _task("t3", kr, ["t2"])]}
    return {"merges": [], "cross_dependencies": []}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8217)
    parser.add_argument("--frontend-origin", default="http://localhost:3217")
    parser.add_argument("--db", type=Path, default=Path(tempfile.gettempdir()) / "okr-e2e.db")
    parser.add_argument(
        "--llm-delay", type=float, default=0.4, help="seconds per LLM call, so progress shows"
    )
    args = parser.parse_args()

    database_url = f"sqlite:///{args.db}"
    password_hash = PasswordHasher().hash(E2E_PASSWORD)
    # app.main builds a default app from the environment when first imported.
    os.environ["DATABASE_URL"] = database_url
    os.environ["APP_PASSWORD_HASH"] = password_hash
    from app.main import create_app
    from tests.api_support import migrate

    args.db.unlink(missing_ok=True)
    engine = create_db_engine(database_url)
    migrate(engine, "head")
    provider = FakeProvider(e2e_llm, delay_seconds=args.llm_delay)

    async def resolver(_: Settings) -> LLMProvider:
        return provider

    settings = Settings(
        app_env="dev",
        database_url=database_url,
        cors_origins=[args.frontend_origin],
        app_password_hash=SecretStr(password_hash),
        openai_api_key=None,
    )
    app = create_app(settings, engine=engine, provider_resolver=resolver)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
