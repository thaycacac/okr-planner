import asyncio
import copy
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from app.planner_llm.providers.base import PipelineStep, Prompt, ProviderHealth, ProviderName

FakeReply = dict[str, Any] | Exception
FakeHandler = Callable[[Prompt, type[BaseModel]], FakeReply]


class FakeProvider:
    """Offline provider for tests: ``handler`` returns a JSON dict or an exception to raise."""

    def __init__(
        self,
        handler: FakeHandler,
        *,
        name: ProviderName = "local",
        model: str = "fake-model",
        max_concurrency: int = 2,
        delay_seconds: float = 0.0,
    ) -> None:
        self.name: ProviderName = name
        self.model = model
        self.max_concurrency = max_concurrency
        self.handler = handler
        self.delay_seconds = delay_seconds
        self.calls: list[Prompt] = []
        self.in_flight = 0
        self.peak_in_flight = 0

    def model_for(self, step: PipelineStep) -> str:
        return f"{self.model}:{step}"

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict[str, Any]:
        self.calls.append(prompt)
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay_seconds)
            reply = self.handler(prompt, schema)
        finally:
            self.in_flight -= 1
        if isinstance(reply, Exception):
            raise reply
        return copy.deepcopy(reply)

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(ok=True, provider=self.name, model=self.model, latency_ms=0)
