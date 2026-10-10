from collections.abc import Mapping
from typing import Any, Literal

import httpx
from pydantic import BaseModel

from app.planner_llm.providers.base import (
    PipelineStep,
    Prompt,
    ProviderHealth,
    ProviderName,
    parse_json_object,
    probe_health,
    strict_json_schema,
)
from app.planner_llm.providers.errors import (
    InvalidJSONError,
    ModelNotFoundError,
    ProviderConnectionError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

LocalApiStyle = Literal["ollama", "openai_compatible"]
MAX_LOCAL_CONCURRENCY = 2
_REACHABILITY_TIMEOUT_SECONDS = 2.0
_THINKING_MODEL_PREFIXES = ("qwen3",)
# Under a JSON grammar a looping model never closes the document; capping the output turns
# that into a fast, retryable truncation instead of a timeout.
DEFAULT_NUM_PREDICT: Mapping[PipelineStep, int] = {
    "clarify": 2048,
    "decompose": 4096,
    # Dedup answers are ids only and capped in number; a valid one stays far below this.
    "dedup": 1024,
}


class LocalProvider:
    """Ollama native ``/api/chat`` by default; ``openai_compatible`` for LM Studio or vLLM."""

    name: ProviderName = "local"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_style: LocalApiStyle = "ollama",
        max_concurrency: int = 1,
        timeout_seconds: float = 180.0,
        num_predict: Mapping[PipelineStep, int] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_style: LocalApiStyle = api_style
        self.max_concurrency = max(1, min(MAX_LOCAL_CONCURRENCY, max_concurrency))
        self.timeout_seconds = timeout_seconds
        self.num_predict: dict[PipelineStep, int] = {**DEFAULT_NUM_PREDICT, **(num_predict or {})}
        self._transport = transport

    def model_for(self, step: PipelineStep) -> str:
        return self.model

    @property
    def disables_thinking(self) -> bool:
        return self.model.lower().startswith(_THINKING_MODEL_PREFIXES)

    def _compat_path(self, resource: str) -> str:
        prefix = "" if self.base_url.endswith("/v1") else "/v1"
        return f"{prefix}/{resource}"

    def _client(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=min(timeout, 5.0)),
            transport=self._transport,
        )

    async def is_reachable(self) -> bool:
        path = "/api/tags" if self.api_style == "ollama" else self._compat_path("models")
        try:
            async with self._client(_REACHABILITY_TIMEOUT_SECONDS) as client:
                response = await client.get(path)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    async def list_models(self) -> list[str]:
        """Model names the runtime reports; empty when it cannot be listed."""
        path = "/api/tags" if self.api_style == "ollama" else self._compat_path("models")
        try:
            async with self._client(_REACHABILITY_TIMEOUT_SECONDS) as client:
                response = await client.get(path)
            payload = response.json() if response.status_code == 200 else {}
        except (httpx.HTTPError, ValueError):
            return []
        key, field = ("models", "name") if self.api_style == "ollama" else ("data", "id")
        items = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []
        return sorted(
            str(item[field]) for item in items if isinstance(item, dict) and item.get(field)
        )

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict[str, Any]:
        json_schema = strict_json_schema(schema)
        messages = [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user},
        ]
        limit = self.num_predict.get(prompt.step)
        if self.api_style == "ollama":
            options: dict[str, Any] = {"temperature": 0}
            if limit:
                options["num_predict"] = limit
            body: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "format": json_schema,
                "stream": False,
                "options": options,
            }
            if self.disables_thinking:
                body["think"] = False
            data = await self._post("/api/chat", body)
            truncated = data.get("done_reason") == "length"
            message = data.get("message")
            content = message.get("content") if isinstance(message, dict) else None
        else:
            body = {
                "model": self.model,
                "messages": messages,
                "temperature": 0,
                "stream": False,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": schema.__name__, "schema": json_schema, "strict": True},
                },
            }
            if limit:
                body["max_tokens"] = limit
            data = await self._post(self._compat_path("chat/completions"), body)
            content, finish_reason = _first_choice(data)
            truncated = finish_reason == "length"
        if truncated:
            raise InvalidJSONError("response truncated at the token limit")
        if content is not None and not isinstance(content, str):
            raise InvalidJSONError("message content is not a string")
        return parse_json_object(content)

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._client(self.timeout_seconds) as client:
                response = await client.post(path, json=body)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"local LLM timed out after {self.timeout_seconds:g}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderConnectionError(
                f"cannot reach local LLM at {self.base_url} ({type(exc).__name__})"
            ) from exc
        if response.status_code == 404:
            raise ModelNotFoundError(f"local LLM returned HTTP 404: {_error_detail(response)}")
        if response.status_code >= 400:
            raise ProviderUnavailableError(
                f"local LLM returned HTTP {response.status_code}: {_error_detail(response)}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderUnavailableError("local LLM returned a non-JSON HTTP body") from exc
        if not isinstance(data, dict):
            raise ProviderUnavailableError("local LLM returned an unexpected HTTP body")
        return data

    async def health_check(self) -> ProviderHealth:
        return await probe_health(self)


def _first_choice(data: dict[str, Any]) -> tuple[Any, Any]:
    """``(content, finish_reason)`` of the first choice."""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise InvalidJSONError("response has no choices")
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return content, choices[0].get("finish_reason")


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.reason_phrase or "error"
    detail = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(detail, dict):
        detail = detail.get("message")
    text = str(detail or response.reason_phrase or "error")
    return text[:200]
