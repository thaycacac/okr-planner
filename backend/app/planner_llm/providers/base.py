import json
import re
import time
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError

from app.planner_llm.providers.errors import (
    InvalidJSONError,
    ModelNotFoundError,
    ProviderAuthError,
    ProviderConnectionError,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
)

ProviderName = Literal["local", "openai", "gemini", "claude"]
PipelineStep = Literal["clarify", "decompose", "dedup", "health_check"]
HealthErrorCode = Literal[
    "connection_failed",
    "model_not_found",
    "invalid_json",
    "unauthorized",
    "timeout",
    "not_configured",
    "unknown",
]


class Prompt(BaseModel):
    step: PipelineStep
    system: str
    user: str
    objective_id: str | None = None
    kr_id: str | None = None
    attempt: int = 0


class ProviderHealth(BaseModel):
    ok: bool
    provider: ProviderName
    model: str
    latency_ms: int | None = None
    error: str | None = None
    error_code: HealthErrorCode | None = None


class LLMProvider(Protocol):
    name: ProviderName
    max_concurrency: int

    def model_for(self, step: PipelineStep) -> str: ...

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict[str, Any]:
        """Return raw JSON constrained by ``schema``; validation and retries live in the caller."""
        ...

    async def health_check(self) -> ProviderHealth: ...


def strict_json_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema accepted by both OpenAI strict Structured Outputs and Ollama ``format``.

    Strict mode requires every property listed in ``required`` and
    ``additionalProperties: false`` on every object.
    """

    def _walk(node: Any) -> Any:
        if isinstance(node, dict):
            node = {k: _walk(v) for k, v in node.items()}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [_walk(v) for v in node]
        return node

    result: dict[str, Any] = _walk(schema.model_json_schema())
    return result


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def parse_json_object(content: str | None) -> dict[str, Any]:
    """Parse a model answer into a JSON object, tolerating think blocks and code fences.

    Error messages describe the position only, never the content.
    """
    if content is None or not content.strip():
        raise InvalidJSONError("empty response")
    text = _THINK_BLOCK.sub("", content).strip()
    fenced = _CODE_FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidJSONError(
            f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from None
    if not isinstance(data, dict):
        raise InvalidJSONError("top-level JSON value must be an object")
    return data


class HealthReply(BaseModel):
    ok: bool


HEALTH_PROMPT = Prompt(
    step="health_check",
    system="You are a connectivity check. Respond only with JSON matching the schema.",
    user='Return {"ok": true}.',
)


_ERROR_CODES: tuple[tuple[type[ProviderError], HealthErrorCode], ...] = (
    (ProviderTimeoutError, "timeout"),
    (ProviderConnectionError, "connection_failed"),
    (ProviderAuthError, "unauthorized"),
    (ProviderNotConfiguredError, "not_configured"),
    (ModelNotFoundError, "model_not_found"),
    (InvalidJSONError, "invalid_json"),
)


def health_error_code(exc: ProviderError) -> HealthErrorCode:
    for error_type, code in _ERROR_CODES:
        if isinstance(exc, error_type):
            return code
    return "unknown"


async def probe_health(provider: LLMProvider) -> ProviderHealth:
    """Send a tiny structured prompt and report latency; never raises."""
    model = provider.model_for("health_check")
    started = time.perf_counter()
    error: str | None = None
    error_code: HealthErrorCode | None = None
    try:
        HealthReply.model_validate(await provider.generate_json(HEALTH_PROMPT, HealthReply))
    except ProviderError as exc:
        error = str(exc) or type(exc).__name__
        error_code = health_error_code(exc)
    except ValidationError:
        error = "unexpected health check response shape"
        error_code = "invalid_json"
    latency_ms = round((time.perf_counter() - started) * 1000)
    return ProviderHealth(
        ok=error is None,
        provider=provider.name,
        model=model,
        latency_ms=latency_ms,
        error=error,
        error_code=error_code,
    )
