from typing import Literal, Protocol

from pydantic import SecretStr

from app.planner_llm.providers.base import LLMProvider
from app.planner_llm.providers.claude_provider import ClaudeCliProvider
from app.planner_llm.providers.gemini_provider import GeminiProvider
from app.planner_llm.providers.local import LocalApiStyle, LocalProvider
from app.planner_llm.providers.openai_provider import OpenAIProvider

ProviderMode = Literal["auto", "local", "openai", "gemini", "claude"]


class LLMSettings(Protocol):
    """Subset of ``app.config.Settings`` the adapters need; keeps this package config-agnostic."""

    @property
    def llm_provider(self) -> ProviderMode: ...
    @property
    def local_llm_base_url(self) -> str: ...
    @property
    def local_llm_api_style(self) -> LocalApiStyle: ...
    @property
    def local_llm_model(self) -> str: ...
    @property
    def local_llm_concurrency(self) -> int: ...
    @property
    def local_llm_timeout_seconds(self) -> float: ...
    @property
    def local_llm_num_predict_clarify(self) -> int: ...
    @property
    def local_llm_num_predict_decompose(self) -> int: ...
    @property
    def local_llm_num_predict_dedup(self) -> int: ...
    @property
    def openai_api_key(self) -> SecretStr | None: ...
    @property
    def openai_model_clarify(self) -> str: ...
    @property
    def openai_model_decompose(self) -> str: ...
    @property
    def openai_model_dedup(self) -> str: ...
    @property
    def openai_concurrency(self) -> int: ...
    @property
    def openai_timeout_seconds(self) -> float: ...
    @property
    def gemini_api_key(self) -> SecretStr | None: ...
    @property
    def gemini_model_clarify(self) -> str: ...
    @property
    def gemini_model_decompose(self) -> str: ...
    @property
    def gemini_model_dedup(self) -> str: ...
    @property
    def gemini_concurrency(self) -> int: ...
    @property
    def gemini_timeout_seconds(self) -> float: ...
    @property
    def claude_cli_path(self) -> str: ...
    @property
    def claude_model_clarify(self) -> str: ...
    @property
    def claude_model_decompose(self) -> str: ...
    @property
    def claude_model_dedup(self) -> str: ...
    @property
    def claude_concurrency(self) -> int: ...
    @property
    def claude_timeout_seconds(self) -> float: ...


def build_local_provider(settings: LLMSettings) -> LocalProvider:
    return LocalProvider(
        base_url=settings.local_llm_base_url,
        model=settings.local_llm_model,
        api_style=settings.local_llm_api_style,
        max_concurrency=settings.local_llm_concurrency,
        timeout_seconds=settings.local_llm_timeout_seconds,
        num_predict={
            "clarify": settings.local_llm_num_predict_clarify,
            "decompose": settings.local_llm_num_predict_decompose,
            "dedup": settings.local_llm_num_predict_dedup,
        },
    )


def build_openai_provider(settings: LLMSettings) -> OpenAIProvider:
    key = settings.openai_api_key
    return OpenAIProvider(
        api_key=key.get_secret_value() if key else None,
        models={
            "clarify": settings.openai_model_clarify,
            "decompose": settings.openai_model_decompose,
            "dedup": settings.openai_model_dedup,
        },
        max_concurrency=settings.openai_concurrency,
        timeout_seconds=settings.openai_timeout_seconds,
    )


def build_gemini_provider(settings: LLMSettings) -> GeminiProvider:
    key = settings.gemini_api_key
    return GeminiProvider(
        api_key=key.get_secret_value() if key else None,
        models={
            "clarify": settings.gemini_model_clarify,
            "decompose": settings.gemini_model_decompose,
            "dedup": settings.gemini_model_dedup,
        },
        max_concurrency=settings.gemini_concurrency,
        timeout_seconds=settings.gemini_timeout_seconds,
    )


def build_claude_provider(settings: LLMSettings) -> ClaudeCliProvider:
    return ClaudeCliProvider(
        cli_path=settings.claude_cli_path,
        models={
            "clarify": settings.claude_model_clarify,
            "decompose": settings.claude_model_decompose,
            "dedup": settings.claude_model_dedup,
        },
        max_concurrency=settings.claude_concurrency,
        timeout_seconds=settings.claude_timeout_seconds,
    )


async def select_provider(settings: LLMSettings, mode: ProviderMode | None = None) -> LLMProvider:
    """Resolve the provider for one run.

    ``mode`` (the choice saved in Settings) overrides ``LLM_PROVIDER``. ``auto`` picks Local
    when it answers the reachability probe, otherwise OpenAI. The decision is made once per
    run; a Local failure later on never switches to OpenAI.
    """
    resolved = mode or settings.llm_provider
    if resolved == "local":
        return build_local_provider(settings)
    if resolved == "openai":
        return build_openai_provider(settings)
    if resolved == "gemini":
        return build_gemini_provider(settings)
    if resolved == "claude":
        return build_claude_provider(settings)
    local = build_local_provider(settings)
    if await local.is_reachable():
        return local
    return build_openai_provider(settings)
