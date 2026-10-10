import ipaddress
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SESSION_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "sqlite:///./okr_planner.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    # "Today" for scheduling is the user's calendar date, not the server's UTC date.
    app_timezone: str = "Asia/Ho_Chi_Minh"

    app_password_hash: SecretStr | None = None
    session_secret: SecretStr = SecretStr(DEV_SESSION_SECRET)
    session_max_age_hours: int = Field(default=7 * 24, ge=1)
    login_max_attempts: int = Field(default=5, ge=1)
    login_lock_seconds: int = Field(default=60, ge=1)
    # Repeated locks double from login_lock_seconds up to this cap.
    login_lock_max_seconds: int = Field(default=15 * 60, ge=1)
    # Peers allowed to report the client IP (the Next.js proxy); empty = use the peer address.
    trusted_proxy_ips: list[str] = []
    # x-forwarded-for: rightmost hop that is not a trusted proxy. Any other header (e.g.
    # x-real-ip set by the platform edge) is read as a single IP.
    client_ip_header: str = "x-forwarded-for"

    llm_provider: Literal["auto", "local", "openai", "gemini", "claude"] = "auto"

    local_llm_base_url: str = "http://localhost:11434"
    local_llm_api_style: Literal["ollama", "openai_compatible"] = "ollama"
    local_llm_model: str = "qwen3:8b"
    local_llm_concurrency: int = 1
    local_llm_timeout_seconds: float = 180.0
    # Cap on generated tokens per step (Ollama num_predict, max_tokens for openai_compatible).
    local_llm_num_predict_clarify: int = Field(default=2048, ge=1)
    local_llm_num_predict_decompose: int = Field(default=4096, ge=1)
    local_llm_num_predict_dedup: int = Field(default=1024, ge=1)

    openai_api_key: SecretStr | None = None
    openai_model_clarify: str = "gpt-4o-mini"
    openai_model_decompose: str = "gpt-4o-mini"
    openai_model_dedup: str = "gpt-4o-mini"
    openai_concurrency: int = 5
    openai_timeout_seconds: float = 60.0

    gemini_api_key: SecretStr | None = None
    gemini_model_clarify: str = "gemini-3.1-flash-lite"
    gemini_model_decompose: str = "gemini-3.1-flash-lite"
    gemini_model_dedup: str = "gemini-3.1-flash-lite"
    gemini_concurrency: int = 5
    gemini_timeout_seconds: float = 60.0

    # Claude through the local `claude` CLI (Claude Code), using the machine's own login.
    claude_cli_path: str = "claude"
    claude_model_clarify: str = "sonnet"
    claude_model_decompose: str = "sonnet"
    claude_model_dedup: str = "haiku"
    claude_concurrency: int = 2
    claude_timeout_seconds: float = 180.0

    llm_max_json_retries: int = 2

    @field_validator("app_password_hash", mode="before")
    @classmethod
    def _blank_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("trusted_proxy_ips")
    @classmethod
    def _valid_networks(cls, values: list[str]) -> list[str]:
        for value in values:
            try:
                ipaddress.ip_network(value)
            except ValueError as exc:
                raise ValueError(f"not an IP address or CIDR network: {value!r}") from exc
        return values

    @field_validator("client_ip_header")
    @classmethod
    def _lower_header(cls, value: str) -> str:
        return value.strip().lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()
