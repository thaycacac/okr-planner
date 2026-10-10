from collections.abc import Mapping
from typing import Any

import openai
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
    ProviderAuthError,
    ProviderConnectionError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenAIProvider:
    """OpenAI Structured Outputs (``strict: true``) with a model per pipeline step."""

    name: ProviderName = "openai"
    label = "OpenAI"
    key_env_var = "OPENAI_API_KEY"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | None = None,
        models: Mapping[PipelineStep, str],
        max_concurrency: int = 5,
        timeout_seconds: float = 60.0,
        client: openai.AsyncOpenAI | None = None,
    ) -> None:
        self._api_key = api_key or None
        self._base_url = base_url
        self._models = dict(models)
        self.max_concurrency = max(1, max_concurrency)
        self.timeout_seconds = timeout_seconds
        self._client = client

    def model_for(self, step: PipelineStep) -> str:
        if step == "health_check":
            step = "clarify"
        return self._models.get(step) or self._models["clarify"]

    def _get_client(self) -> openai.AsyncOpenAI:
        if self._client is None:
            if not self._api_key:
                raise ProviderNotConfiguredError(f"{self.key_env_var} is not configured")
            self._client = openai.AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self.timeout_seconds,
                max_retries=2,
            )
        return self._client

    async def generate_json(self, prompt: Prompt, schema: type[BaseModel]) -> dict[str, Any]:
        client = self._get_client()
        model = self.model_for(prompt.step)
        try:
            completion = await client.chat.completions.create(
                model=model,
                temperature=0,
                messages=[
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": strict_json_schema(schema),
                        "strict": True,
                    },
                },
            )
        except openai.APITimeoutError as exc:
            raise ProviderTimeoutError(
                f"{self.label} timed out after {self.timeout_seconds:g}s"
            ) from exc
        except openai.APIConnectionError as exc:
            raise ProviderConnectionError(f"cannot reach {self.label} API") from exc
        except openai.AuthenticationError as exc:
            raise ProviderAuthError(f"{self.label} rejected the API key") from exc
        except openai.NotFoundError as exc:
            raise ModelNotFoundError(f"{self.label} model {model!r} not found") from exc
        except openai.APIStatusError as exc:
            raise ProviderUnavailableError(
                f"{self.label} returned HTTP {exc.status_code}: {str(exc.message)[:200]}"
            ) from exc

        if not completion.choices:
            raise InvalidJSONError("response has no choices")
        choice = completion.choices[0]
        if choice.message.refusal:
            raise InvalidJSONError("model refused to answer")
        if choice.finish_reason == "length":
            raise InvalidJSONError("response truncated at the token limit")
        return parse_json_object(choice.message.content)

    async def health_check(self) -> ProviderHealth:
        return await probe_health(self)
