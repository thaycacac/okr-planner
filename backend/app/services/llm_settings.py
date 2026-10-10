"""Provider choice saved in the database, layered over the environment defaults (ADR 0002)."""

import shutil
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.api.schemas import (
    LlmProviderName,
    LlmSettings,
    LlmSettingsUpdate,
    LlmTestErrorCode,
    LlmTestRequest,
    LlmTestResult,
    LocalApiStyle,
)
from app.config import Settings
from app.persistence.models import AppSettings
from app.planner_llm.providers import (
    LLMProvider,
    LocalProvider,
    ProviderHealth,
    build_claude_provider,
    build_gemini_provider,
    build_openai_provider,
)

SETTINGS_ROW_ID = 1
TEST_TIMEOUT_SECONDS = 60.0


def _row(session: Session) -> AppSettings:
    row = session.get(AppSettings, SETTINGS_ROW_ID)
    if row is None:
        row = AppSettings(id=SETTINGS_ROW_ID)
        session.add(row)
        session.flush()
    return row


def effective_settings(session: Session, base: Settings) -> Settings:
    """Environment settings with the choices saved in Settings applied on top."""
    row = session.get(AppSettings, SETTINGS_ROW_ID)
    if row is None:
        return base
    update: dict[str, Any] = {}
    if row.llm_provider:
        update["llm_provider"] = row.llm_provider
    if row.local_base_url:
        update["local_llm_base_url"] = row.local_base_url
    if row.local_model:
        update["local_llm_model"] = row.local_model
    if row.local_api_style:
        update["local_llm_api_style"] = row.local_api_style
    if row.openai_api_key:
        update["openai_api_key"] = SecretStr(row.openai_api_key)
    if row.gemini_api_key:
        update["gemini_api_key"] = SecretStr(row.gemini_api_key)
    return base.model_copy(update=update)


def to_schema(settings: Settings, row: AppSettings | None = None) -> LlmSettings:
    # "auto" only exists in the environment; the UI shows the provider auto prefers.
    provider = LlmProviderName.local
    if settings.llm_provider in ("openai", "gemini", "claude"):
        provider = LlmProviderName(settings.llm_provider)
    return LlmSettings(
        provider=provider,
        local_base_url=settings.local_llm_base_url,
        local_model=settings.local_llm_model,
        local_api_style=LocalApiStyle(settings.local_llm_api_style),
        openai_model=settings.openai_model_decompose,
        openai_api_key_configured=bool(
            settings.openai_api_key and settings.openai_api_key.get_secret_value()
        ),
        openai_api_key_saved=bool(row and row.openai_api_key),
        gemini_api_key_saved=bool(row and row.gemini_api_key),
        gemini_model=settings.gemini_model_decompose,
        gemini_api_key_configured=bool(
            settings.gemini_api_key and settings.gemini_api_key.get_secret_value()
        ),
        claude_model=settings.claude_model_decompose,
        claude_cli_available=shutil.which(settings.claude_cli_path) is not None,
    )


def read(session: Session, base: Settings) -> LlmSettings:
    return to_schema(effective_settings(session, base), session.get(AppSettings, SETTINGS_ROW_ID))


def update(session: Session, base: Settings, body: LlmSettingsUpdate) -> LlmSettings:
    row = _row(session)
    row.llm_provider = body.provider.value
    row.local_base_url = body.local_base_url
    row.local_model = body.local_model
    row.local_api_style = body.local_api_style.value
    if body.openai_api_key is not None:
        row.openai_api_key = body.openai_api_key.strip() or None
    if body.gemini_api_key is not None:
        row.gemini_api_key = body.gemini_api_key.strip() or None
    session.commit()
    return read(session, base)


def _same_model(wanted: str, available: str) -> bool:
    """Ollama lists ``name:tag``; a bare name means ``:latest``."""
    if wanted == available:
        return True
    return ":" not in wanted and available == f"{wanted}:latest"


def _remote_result(provider: LlmProviderName, health: ProviderHealth) -> LlmTestResult:
    return LlmTestResult(
        ok=health.ok,
        provider=provider,
        model=health.model,
        latency_ms=health.latency_ms,
        error=health.error,
        error_code=LlmTestErrorCode(health.error_code) if health.error_code else None,
        available_models=[health.model] if health.ok else [],
    )


async def test_connection(
    settings: Settings, body: LlmTestRequest, transport: httpx.AsyncBaseTransport | None = None
) -> LlmTestResult:
    """Probe the values in the form (possibly unsaved) without touching the database."""
    remote: dict[LlmProviderName, Callable[[Settings], LLMProvider]] = {
        LlmProviderName.openai: build_openai_provider,
        LlmProviderName.gemini: build_gemini_provider,
        LlmProviderName.claude: build_claude_provider,
    }
    if body.provider in remote:
        # Keys typed in the form win over the stored ones so they can be tried before saving.
        typed = {"openai": body.openai_api_key, "gemini": body.gemini_api_key}.get(body.provider)
        if typed and typed.strip():
            settings = settings.model_copy(
                update={f"{body.provider.value}_api_key": SecretStr(typed.strip())}
            )
        health = await remote[body.provider](settings).health_check()
        return _remote_result(body.provider, health)

    local = LocalProvider(
        base_url=body.local_base_url or settings.local_llm_base_url,
        model=body.local_model or settings.local_llm_model,
        api_style=(body.local_api_style or LocalApiStyle(settings.local_llm_api_style)).value,
        timeout_seconds=min(settings.local_llm_timeout_seconds, TEST_TIMEOUT_SECONDS),
        transport=transport,
    )
    models = await local.list_models()
    if models and not any(_same_model(local.model, m) for m in models):
        return LlmTestResult(
            ok=False,
            provider=LlmProviderName.local,
            model=local.model,
            latency_ms=None,
            error=f"model {local.model!r} is not installed",
            error_code=LlmTestErrorCode.model_not_found,
            available_models=models,
        )
    health = await local.health_check()
    return LlmTestResult(
        ok=health.ok,
        provider=LlmProviderName.local,
        model=health.model,
        latency_ms=health.latency_ms,
        error=health.error,
        error_code=LlmTestErrorCode(health.error_code) if health.error_code else None,
        available_models=models,
    )
