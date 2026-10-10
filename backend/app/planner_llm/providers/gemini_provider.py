from app.planner_llm.providers.base import ProviderName
from app.planner_llm.providers.openai_provider import OpenAIProvider

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiProvider(OpenAIProvider):
    """Gemini through Google's OpenAI-compatible endpoint; same Structured Outputs contract."""

    name: ProviderName = "gemini"
    label = "Gemini"
    key_env_var = "GEMINI_API_KEY"

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("base_url", GEMINI_OPENAI_BASE_URL)
        super().__init__(**kwargs)  # type: ignore[arg-type]
