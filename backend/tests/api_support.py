import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from pydantic import BaseModel, SecretStr
from sqlalchemy import Engine

from app.config import Settings
from app.main import create_app
from app.planner_llm import LLMProvider
from app.planner_llm.providers.base import Prompt
from app.planner_llm.providers.fake import FakeProvider, FakeReply
from app.planner_llm.schemas import KeyResultCheck, KeyResultNeedsOutput

BACKEND_DIR = Path(__file__).resolve().parent.parent

TEST_PASSWORD = "correct horse battery staple"
# Cheap parameters keep each verification in the microseconds; the format is still argon2id.
TEST_PASSWORD_HASH = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(TEST_PASSWORD)


class FakeClock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def with_password(settings: Settings) -> Settings:
    if settings.app_password_hash is not None:
        return settings
    return settings.model_copy(update={"app_password_hash": SecretStr(TEST_PASSWORD_HASH)})


def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "app/persistence/migrations"))
    return config


def migrate(engine: Engine, revision: str, *, down: bool = False) -> None:
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        if down:
            command.downgrade(config, revision)
        else:
            command.upgrade(config, revision)


def llm_task(
    local_id: str, kr_id: str, hours: float = 4, deps: list[str] | None = None
) -> dict[str, Any]:
    return {
        "local_id": local_id,
        "title": f"Task {local_id} for {kr_id}",
        "description": "Do the work",
        "estimate_hours": hours,
        "done_criteria": "Reviewed",
        "depends_on": deps or [],
        "kr_id": kr_id,
    }


@dataclass
class ScriptedLLM:
    """Until the first question is asked every KR looks vague and clarify asks one open
    question, then all KRs look clear; decompose returns two dependent tasks per KR; dedup
    changes nothing."""

    clarify_question: str | None = "Bạn có thể dành bao nhiêu giờ mỗi ngày?"
    clarify_calls: int = 0
    overrides: dict[str, FakeReply] = field(default_factory=dict)

    def __call__(self, prompt: Prompt, schema: type[BaseModel]) -> FakeReply:
        if prompt.step in self.overrides:
            return self.overrides[prompt.step]
        if schema is KeyResultCheck:
            vague = bool(self.clarify_question) and not self.clarify_calls
            return {"end_result": "", "concrete": not vague}
        if schema is KeyResultNeedsOutput:
            return {"needs": []}
        if prompt.step == "clarify":
            self.clarify_calls += 1
            return {
                "status": "needs_clarification",
                "questions": [
                    {"kr_id": None, "question": self.clarify_question, "reason": "capacity"}
                ],
            }
        if prompt.step == "decompose":
            assert prompt.kr_id is not None
            return {
                "tasks": [
                    llm_task("t1", prompt.kr_id, 4),
                    llm_task("t2", prompt.kr_id, 3, ["t1"]),
                ]
            }
        if prompt.step == "dedup":
            return {"merges": [], "cross_dependencies": []}
        return {"ok": True}


@dataclass
class ApiHarness:
    client: TestClient
    llm: ScriptedLLM
    provider: FakeProvider

    @classmethod
    @contextmanager
    def start(
        cls,
        engine: Engine,
        *,
        today: date,
        settings: Settings | None = None,
        llm_transport: httpx.AsyncBaseTransport | None = None,
    ) -> Iterator["ApiHarness"]:
        llm = ScriptedLLM()
        provider = FakeProvider(llm)

        async def resolver(_: Settings) -> LLMProvider:
            return provider

        app = create_app(
            with_password(settings or Settings(database_url=str(engine.url), openai_api_key=None)),
            engine=engine,
            provider_resolver=resolver,
            today=lambda: today,
            llm_transport=llm_transport,
        )
        with TestClient(app) as client:
            assert client.post("/auth/login", json={"password": TEST_PASSWORD}).status_code == 200
            yield cls(client=client, llm=llm, provider=provider)

    def events(self, job_id: str, last_event_id: int | None = None) -> list[dict[str, Any]]:
        headers = {"Last-Event-ID": str(last_event_id)} if last_event_id is not None else {}
        with self.client.stream("GET", f"/plans/{job_id}/events", headers=headers) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = "".join(response.iter_text())
        events = []
        for block in body.split("\n\n"):
            data = [line[6:] for line in block.splitlines() if line.startswith("data: ")]
            if data:
                events.append(json.loads("".join(data)))
        return events
