import json
from collections.abc import Callable
from typing import Any

import httpx
import openai
import pytest
from pydantic import SecretStr

from app.config import Settings
from app.planner_llm.providers import (
    InvalidJSONError,
    LocalProvider,
    OpenAIProvider,
    Prompt,
    ProviderUnavailableError,
    build_local_provider,
    select_provider,
)
from app.planner_llm.schemas import DecomposeOutput

PROMPT = Prompt(step="decompose", system="sys", user="usr", kr_id="kr1")
Handler = Callable[[httpx.Request], httpx.Response]


class Recorder:
    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)

    def body(self, index: int = -1) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(self.requests[index].content)
        return data


def _local(recorder: Recorder, **kwargs: Any) -> LocalProvider:
    params: dict[str, Any] = {"base_url": "http://ollama:11434", "model": "qwen3:8b"}
    params.update(kwargs)
    return LocalProvider(transport=httpx.MockTransport(recorder), **params)


def _ollama_reply(content: str) -> Handler:
    return lambda _: httpx.Response(
        200, json={"message": {"role": "assistant", "content": content}}
    )


async def test_ollama_request_uses_schema_format_temperature_zero_and_no_thinking() -> None:
    recorder = Recorder(_ollama_reply('{"tasks": []}'))

    data = await _local(recorder).generate_json(PROMPT, DecomposeOutput)

    assert data == {"tasks": []}
    request = recorder.requests[0]
    assert request.url.path == "/api/chat"
    body = recorder.body()
    assert body["stream"] is False
    assert body["options"] == {"temperature": 0, "num_predict": 4096}
    assert body["think"] is False
    assert body["format"]["additionalProperties"] is False
    assert body["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]


async def test_ollama_keeps_default_thinking_flag_for_other_models() -> None:
    recorder = Recorder(_ollama_reply('{"tasks": []}'))

    await _local(recorder, model="qwen2.5:3b").generate_json(PROMPT, DecomposeOutput)

    assert "think" not in recorder.body()


async def test_ollama_caps_generated_tokens_per_step() -> None:
    recorder = Recorder(_ollama_reply("{}"))
    provider = _local(recorder, num_predict={"decompose": 1000})

    for step in ("clarify", "decompose", "dedup", "health_check"):
        await provider.generate_json(PROMPT.model_copy(update={"step": step}), DecomposeOutput)

    sent = [recorder.body(i)["options"].get("num_predict") for i in range(4)]
    assert sent == [2048, 1000, 1024, None]


async def test_ollama_truncated_answer_is_invalid_json() -> None:
    recorder = Recorder(
        lambda _: httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": '{"ta'}, "done_reason": "length"},
        )
    )

    with pytest.raises(InvalidJSONError, match="truncated"):
        await _local(recorder).generate_json(PROMPT, DecomposeOutput)


async def test_openai_compatible_caps_tokens_and_detects_truncation() -> None:
    recorder = Recorder(
        lambda _: httpx.Response(
            200, json={"choices": [{"message": {"content": '{"ta'}, "finish_reason": "length"}]}
        )
    )
    provider = _local(recorder, api_style="openai_compatible", model="m")

    with pytest.raises(InvalidJSONError, match="truncated"):
        await provider.generate_json(PROMPT, DecomposeOutput)
    assert recorder.body()["max_tokens"] == 4096


def test_num_predict_is_read_from_settings() -> None:
    settings = Settings(
        local_llm_num_predict_clarify=100,
        local_llm_num_predict_decompose=200,
        local_llm_num_predict_dedup=300,
    )

    provider = build_local_provider(settings)

    assert provider.num_predict == {"clarify": 100, "decompose": 200, "dedup": 300}


async def test_openai_compatible_mode_posts_json_schema_response_format() -> None:
    recorder = Recorder(
        lambda _: httpx.Response(200, json={"choices": [{"message": {"content": '{"tasks": []}'}}]})
    )
    provider = _local(
        recorder, base_url="http://lmstudio:1234/v1", api_style="openai_compatible", model="m"
    )

    await provider.generate_json(PROMPT, DecomposeOutput)

    assert recorder.requests[0].url.path == "/v1/chat/completions"
    body = recorder.body()
    assert body["temperature"] == 0
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["response_format"]["json_schema"]["name"] == "DecomposeOutput"


async def test_local_http_error_is_unavailable_with_detail() -> None:
    recorder = Recorder(lambda _: httpx.Response(404, json={"error": "model 'x' not found"}))

    with pytest.raises(ProviderUnavailableError, match="HTTP 404: model 'x' not found"):
        await _local(recorder).generate_json(PROMPT, DecomposeOutput)


async def test_local_connection_error_is_unavailable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    provider = _local(Recorder(refuse))

    with pytest.raises(ProviderUnavailableError, match="cannot reach local LLM"):
        await provider.generate_json(PROMPT, DecomposeOutput)
    assert await provider.is_reachable() is False


async def test_local_non_json_content_is_invalid_json() -> None:
    with pytest.raises(InvalidJSONError):
        await _local(Recorder(_ollama_reply("Sure! Here are tasks"))).generate_json(
            PROMPT, DecomposeOutput
        )


async def test_local_concurrency_is_clamped() -> None:
    recorder = Recorder(_ollama_reply("{}"))
    assert _local(recorder, max_concurrency=8).max_concurrency == 2
    assert _local(recorder, max_concurrency=0).max_concurrency == 1


async def test_health_check_reports_latency_and_error() -> None:
    ok = await _local(Recorder(_ollama_reply('{"ok": true}'))).health_check()
    assert ok.ok is True
    assert ok.provider == "local"
    assert ok.model == "qwen3:8b"
    assert ok.latency_ms is not None

    down = await _local(
        Recorder(lambda _: httpx.Response(500, json={"error": "boom"}))
    ).health_check()
    assert down.ok is False
    assert down.error == "local LLM returned HTTP 500: boom"


def _openai(recorder: Recorder) -> OpenAIProvider:
    client = openai.AsyncOpenAI(
        api_key="sk-test",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(recorder)),
    )
    return OpenAIProvider(
        api_key="sk-test",
        models={"clarify": "gpt-c", "decompose": "gpt-d", "dedup": "gpt-x"},
        client=client,
    )


def _completion(content: str, finish_reason: str = "stop") -> dict[str, Any]:
    return {
        "id": "c1",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-d",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content, "refusal": None},
            }
        ],
    }


async def test_openai_uses_strict_structured_outputs_and_step_model() -> None:
    recorder = Recorder(lambda _: httpx.Response(200, json=_completion('{"tasks": []}')))

    data = await _openai(recorder).generate_json(PROMPT, DecomposeOutput)

    assert data == {"tasks": []}
    body = recorder.body()
    assert body["model"] == "gpt-d"
    assert body["temperature"] == 0
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False


async def test_openai_truncated_answer_is_invalid_json() -> None:
    recorder = Recorder(lambda _: httpx.Response(200, json=_completion('{"ta', "length")))

    with pytest.raises(InvalidJSONError, match="truncated"):
        await _openai(recorder).generate_json(PROMPT, DecomposeOutput)


async def test_openai_auth_error_is_unavailable() -> None:
    recorder = Recorder(lambda _: httpx.Response(401, json={"error": {"message": "bad key"}}))

    with pytest.raises(ProviderUnavailableError, match="rejected the API key"):
        await _openai(recorder).generate_json(PROMPT, DecomposeOutput)


async def test_openai_without_key_reports_unhealthy() -> None:
    provider = OpenAIProvider(api_key=None, models={"clarify": "gpt-4o-mini"})

    health = await provider.health_check()

    assert health.ok is False
    assert health.provider == "openai"
    assert health.model == "gpt-4o-mini"
    assert health.error == "OPENAI_API_KEY is not configured"


async def test_select_provider_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(llm_provider="auto", openai_api_key=SecretStr("sk-test"))

    async def reachable(self: LocalProvider) -> bool:
        return True

    async def unreachable(self: LocalProvider) -> bool:
        return False

    monkeypatch.setattr(LocalProvider, "is_reachable", reachable)
    assert (await select_provider(settings)).name == "local"
    assert (await select_provider(settings, "openai")).name == "openai"

    monkeypatch.setattr(LocalProvider, "is_reachable", unreachable)
    assert (await select_provider(settings)).name == "openai"
    assert (await select_provider(settings, "local")).name == "local"
