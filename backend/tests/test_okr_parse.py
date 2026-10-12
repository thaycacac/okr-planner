"""Free-text OKR structuring: output normalization and the ``POST /okr/parse`` endpoint."""

from datetime import date
from typing import Any

from app.planner_llm.okr_parse import ParsedKr, ParsedObjective, ParsedOkr, normalize
from app.planner_llm.providers.errors import ProviderConnectionError
from tests.api_support import ApiHarness

Q4_START, Q4_END = date(2026, 10, 1), date(2026, 12, 31)


def kr(**fields: Any) -> dict[str, Any]:
    base = {
        "text": "Reach it",
        "kind": "other",
        "baseline": None,
        "target": None,
        "unit": None,
        "due_date": None,
        "note": None,
    }
    return {**base, **fields}


def reply(*krs: dict[str, Any], title: str = "Grow") -> dict[str, Any]:
    return {"objectives": [{"title": title, "priority": "medium", "key_results": list(krs)}]}


def test_normalize_repairs_mismatched_fields() -> None:
    parsed = ParsedOkr(
        objectives=[
            ParsedObjective(
                title=" Grow ",
                priority="high",
                key_results=[
                    ParsedKr(
                        **kr(text="1000 clicks", kind="numeric", target=1000, unit=" clicks ")
                    ),
                    ParsedKr(**kr(text="no target", kind="numeric")),
                    ParsedKr(**kr(text="ship", kind="milestone", due_date="2026-10-20")),
                    ParsedKr(**kr(text="late", kind="milestone", due_date="2027-01-05")),
                    ParsedKr(**kr(text="  ", kind="other")),
                ],
            ),
            ParsedObjective(title="", priority="low", key_results=[]),
        ]
    )
    result = normalize(parsed, Q4_START, Q4_END)
    assert [o.title for o in result.objectives] == ["Grow"]
    krs = result.objectives[0].key_results
    assert [k.kind for k in krs] == ["numeric", "other", "milestone", "other"]
    assert (krs[0].baseline, krs[0].target, krs[0].unit) == (0.0, 1000, "clicks")
    assert krs[2].due_date == "2026-10-20"
    assert krs[3].due_date is None


def test_parse_endpoint_returns_structured_okrs(api: ApiHarness) -> None:
    api.llm.overrides["decompose"] = reply(
        kr(text="Đạt 1.000 lượt nhấp trong 28 ngày", kind="numeric", target=1000, unit="lượt nhấp"),
        kr(text="Ra mắt bản beta", kind="milestone", due_date="2026-10-20"),
    )
    response = api.client.post(
        "/okr/parse", json={"text": "O1: Grow\nKR1: ...", "year": 2026, "number": 4}
    )
    assert response.status_code == 200, response.text
    krs = response.json()["objectives"][0]["key_results"]
    assert krs[0] == {
        "text": "Đạt 1.000 lượt nhấp trong 28 ngày",
        "kind": "numeric",
        "baseline": 0.0,
        "target": 1000.0,
        "unit": "lượt nhấp",
        "due_date": None,
        "note": None,
    }
    assert krs[1]["kind"] == "milestone"
    assert krs[1]["due_date"] == "2026-10-20"
    prompt = api.provider.calls[-1]
    assert "2026-10-01" in prompt.user
    assert "2026-12-31" in prompt.user


def test_parse_endpoint_retries_once_on_invalid_output(api: ApiHarness) -> None:
    answers = iter([{"unexpected": True}, reply(kr(text="Ship it"))])
    api.provider.handler = lambda _prompt, _schema: next(answers)
    response = api.client.post("/okr/parse", json={"text": "Ship it", "year": 2026, "number": 4})
    assert response.status_code == 200
    assert len(api.provider.calls) == 2


def test_parse_endpoint_reports_provider_failures(api: ApiHarness) -> None:
    api.provider.handler = lambda _prompt, _schema: ProviderConnectionError("cannot reach Ollama")
    response = api.client.post("/okr/parse", json={"text": "Ship it", "year": 2026, "number": 4})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "llm_unavailable"
    assert "Ship it" not in response.text

    api.provider.handler = lambda _prompt, _schema: {"nope": 1}
    bad = api.client.post("/okr/parse", json={"text": "Ship it", "year": 2026, "number": 4})
    assert bad.status_code == 502
    assert bad.json()["detail"]["code"] == "llm_invalid_output"


def test_parse_endpoint_validates_the_request(api: ApiHarness) -> None:
    assert (
        api.client.post("/okr/parse", json={"text": "", "year": 2026, "number": 4}).status_code
        == 422
    )
    assert (
        api.client.post("/okr/parse", json={"text": "x", "year": 2026, "number": 5}).status_code
        == 422
    )
