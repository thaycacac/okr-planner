from collections.abc import Callable

import httpx
from sqlalchemy import Engine

from app.config import Settings
from tests.api_support import ApiHarness
from tests.conftest import TODAY

WEEKDAYS = {"mon": 240, "tue": 240, "wed": 240, "thu": 240, "fri": 240, "sat": 0, "sun": 0}


def test_calendar_settings_round_trip(api: ApiHarness) -> None:
    assert api.client.get("/settings/calendar").json() == {
        "capacity_minutes": WEEKDAYS,
        "work_saturday": False,
        "work_sunday": False,
        "work_holidays": False,
    }
    body = {
        "capacity_minutes": {**WEEKDAYS, "mon": 480, "sat": 120},
        "work_saturday": True,
        "work_sunday": False,
        "work_holidays": True,
    }
    assert api.client.put("/settings/calendar", json=body).json() == body
    assert api.client.get("/settings/calendar").json() == body


def test_calendar_settings_are_validated(api: ApiHarness) -> None:
    too_long = {"capacity_minutes": {**WEEKDAYS, "mon": 721}}
    body = {"work_saturday": False, "work_sunday": False, "work_holidays": False}
    assert api.client.put("/settings/calendar", json={**body, **too_long}).status_code == 422
    missing_day = {"capacity_minutes": {k: v for k, v in WEEKDAYS.items() if k != "sun"}}
    assert api.client.put("/settings/calendar", json={**body, **missing_day}).status_code == 422


def test_llm_settings_default_to_environment_then_saved_choice(api: ApiHarness) -> None:
    initial = api.client.get("/settings/llm").json()
    # Depend on the developer's .env and on whether `claude` is installed.
    for machine_specific in ("gemini_api_key_configured", "claude_cli_available"):
        assert isinstance(initial.pop(machine_specific), bool)
    assert initial.pop("openai_api_key_saved") is False
    assert initial.pop("gemini_api_key_saved") is False
    assert initial == {
        "provider": "local",
        "local_base_url": "http://localhost:11434",
        "local_model": "qwen3:8b",
        "local_api_style": "ollama",
        "openai_model": "gpt-4o-mini",
        "openai_api_key_configured": False,
        "gemini_model": "gemini-3.1-flash-lite",
        "claude_model": "sonnet",
    }
    update = {
        "provider": "openai",
        "local_base_url": "http://gpu-box:1234/",
        "local_model": "qwen2.5:7b-instruct",
        "local_api_style": "openai_compatible",
    }
    saved = api.client.put("/settings/llm", json=update).json()
    expected = {**initial, **update, "local_base_url": "http://gpu-box:1234"}
    assert {k: v for k, v in saved.items() if k in expected} == expected
    assert api.client.get("/settings/llm").json() == saved

    bad_url = {**update, "local_base_url": "file:///etc/passwd"}
    assert api.client.put("/settings/llm", json=bad_url).status_code == 422


def test_api_keys_are_saved_but_never_returned(api: ApiHarness) -> None:
    body = {
        "provider": "gemini",
        "local_base_url": "http://localhost:11434",
        "local_model": "qwen3:8b",
        "local_api_style": "ollama",
        "gemini_api_key": "  secret-gemini-key  ",
    }
    response = api.client.put("/settings/llm", json=body)
    assert response.status_code == 200
    saved = response.json()
    assert saved["gemini_api_key_saved"] is True
    assert saved["gemini_api_key_configured"] is True
    assert saved["openai_api_key_saved"] is False
    assert "secret-gemini-key" not in response.text
    assert "secret-gemini-key" not in api.client.get("/settings/llm").text

    # Omitting the key keeps it; an empty string removes it.
    body.pop("gemini_api_key")
    assert api.client.put("/settings/llm", json=body).json()["gemini_api_key_saved"] is True
    cleared = api.client.put("/settings/llm", json={**body, "gemini_api_key": ""}).json()
    assert cleared["gemini_api_key_saved"] is False


def _ollama(
    models: list[str], chat: Callable[[httpx.Request], httpx.Response]
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": m} for m in models]})
        return chat(request)

    return httpx.MockTransport(handler)


def _ok_chat(_: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"message": {"content": '{"ok": true}'}})


def test_llm_test_reports_success_and_installed_models(db_engine: Engine) -> None:
    transport = _ollama(["llama3.1:8b", "qwen3:8b"], _ok_chat)
    with ApiHarness.start(db_engine, today=TODAY, llm_transport=transport) as api:
        result = api.client.post("/settings/llm/test", json={"provider": "local"}).json()
    assert result["ok"] is True
    assert result["model"] == "qwen3:8b"
    assert result["error_code"] is None
    assert result["available_models"] == ["llama3.1:8b", "qwen3:8b"]
    assert result["latency_ms"] >= 0


def test_llm_test_detects_missing_model_before_calling_it(db_engine: Engine) -> None:
    def chat(_: httpx.Request) -> httpx.Response:
        raise AssertionError("chat must not be called")

    transport = _ollama(["llama3.1:8b"], chat)
    with ApiHarness.start(db_engine, today=TODAY, llm_transport=transport) as api:
        result = api.client.post(
            "/settings/llm/test", json={"provider": "local", "local_model": "qwen3:8b"}
        ).json()
    assert (result["ok"], result["error_code"]) == (False, "model_not_found")
    assert result["available_models"] == ["llama3.1:8b"]


def test_llm_test_classifies_connection_failures(db_engine: Engine) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    transport = httpx.MockTransport(refuse)
    with ApiHarness.start(db_engine, today=TODAY, llm_transport=transport) as api:
        result = api.client.post(
            "/settings/llm/test",
            json={"provider": "local", "local_base_url": "http://127.0.0.1:9"},
        ).json()
    assert (result["ok"], result["error_code"]) == (False, "connection_failed")
    assert result["available_models"] == []
    assert "127.0.0.1:9" in result["error"]


def test_llm_test_openai_without_key_is_not_configured(db_engine: Engine) -> None:
    settings = Settings(database_url=str(db_engine.url), openai_api_key=None)
    with ApiHarness.start(db_engine, today=TODAY, settings=settings) as api:
        result = api.client.post("/settings/llm/test", json={"provider": "openai"}).json()
    assert result == {
        "ok": False,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "latency_ms": result["latency_ms"],
        "error": "OPENAI_API_KEY is not configured",
        "error_code": "not_configured",
        "available_models": [],
    }
