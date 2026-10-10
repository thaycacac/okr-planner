"""The frontend generates its API types from this schema; names and shapes must stay stable."""

import json
from pathlib import Path
from typing import Any

import pytest

from app.main import create_app

FRONTEND_SNAPSHOT = Path(__file__).resolve().parents[2] / "frontend/openapi/openapi.json"
SHARED_SCHEMAS = (
    "ErrorDetail",
    "ErrorResponse",
    "LoginRequest",
    "SessionInfo",
    "WeekdayCapacity",
    "CalendarSettings",
    "LlmProviderName",
    "LocalApiStyle",
    "LlmSettings",
    "LlmSettingsUpdate",
    "LlmTestRequest",
    "LlmTestErrorCode",
    "LlmTestResult",
    "KeyResultOut",
    "FeasibilityOut",
    "OptionKind",
    "OptionGroup",
    "OptionEffectCode",
    "OptionOutcome",
    "OptionEffect",
    "OverloadOption",
    "WeekdayHint",
    "OverloadOptions",
    "OptionSelection",
    "OptionEvaluation",
    "OptionApplication",
)


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return create_app().openapi()


def test_schema_names_are_stable(spec: dict[str, Any]) -> None:
    names = set(spec["components"]["schemas"])
    assert not [n for n in names if n.endswith(("-Input", "-Output")) or "__" in n]
    assert {
        "QuarterDetail",
        "ObjectiveOut",
        "KeyResultOut",
        "TaskOut",
        "PlanJob",
        "PlanEvent",
        "PlanRunDetail",
        "QuarterSchedule",
        *SHARED_SCHEMAS,
    } <= names


def test_plan_routes_are_published(spec: dict[str, Any]) -> None:
    paths = spec["paths"]
    for path, method in [
        ("/auth/login", "post"),
        ("/auth/logout", "post"),
        ("/auth/me", "get"),
        ("/quarters", "post"),
        ("/quarters/{quarter_id}/objectives", "post"),
        ("/objectives/{objective_id}/key-results", "post"),
        ("/quarters/{quarter_id}/tasks", "get"),
        ("/plans", "post"),
        ("/plans/{job_id}", "get"),
        ("/plans/{job_id}/answers", "post"),
        ("/plans/{job_id}/resume", "post"),
        ("/plans/{job_id}/cancel", "post"),
        ("/quarters/{quarter_id}/schedule", "get"),
        ("/settings/calendar", "put"),
        ("/settings/llm", "put"),
        ("/settings/llm/test", "post"),
        ("/quarters/{quarter_id}/options", "get"),
        ("/quarters/{quarter_id}/options/evaluate", "post"),
        ("/quarters/{quarter_id}/options/apply", "post"),
        ("/option-applications/{application_id}/undo", "post"),
        ("/quarters/{quarter_id}/export", "get"),
    ]:
        assert method in paths[path], f"{method.upper()} {path}"
    events = paths["/plans/{job_id}/events"]["get"]["responses"]["200"]["content"]
    assert events["text/event-stream"]["schema"] == {"$ref": "#/components/schemas/PlanEvent"}


def test_option_and_export_routes_document_their_contract(spec: dict[str, Any]) -> None:
    paths = spec["paths"]
    apply = paths["/quarters/{quarter_id}/options/apply"]["post"]
    header = next(p for p in apply["parameters"] if p["in"] == "header")
    assert (header["name"], header["required"]) == ("Idempotency-Key", True)
    assert {"404", "409", "422"} <= set(apply["responses"])
    assert {"404", "409", "422"} <= set(
        paths["/option-applications/{application_id}/undo"]["post"]["responses"]
    )

    export = paths["/quarters/{quarter_id}/export"]["get"]
    assert {p["name"] for p in export["parameters"]} >= {"format", "sheet", "lang", "details"}
    content = export["responses"]["200"]["content"]
    assert set(content) == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv; charset=utf-8",
    }


def test_protected_routes_document_401(spec: dict[str, Any]) -> None:
    public = {"/health", "/ready", "/auth/login", "/auth/logout"}
    missing = [
        f"{method.upper()} {path}"
        for path, operations in spec["paths"].items()
        if path not in public
        for method, operation in operations.items()
        if "401" not in operation["responses"]
    ]
    assert missing == []


def _shape(schema: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(sorted(schema.get("properties", {}))),
        tuple(sorted(schema.get("required", []))),
        tuple(schema.get("enum", [])),
    )


@pytest.mark.skipif(not FRONTEND_SNAPSHOT.is_file(), reason="frontend snapshot not checked out")
def test_settings_schemas_match_the_frontend_snapshot(spec: dict[str, Any]) -> None:
    frontend = json.loads(FRONTEND_SNAPSHOT.read_text(encoding="utf-8"))["components"]["schemas"]
    backend = spec["components"]["schemas"]
    mismatched = [
        name for name in SHARED_SCHEMAS if _shape(backend[name]) != _shape(frontend[name])
    ]
    assert mismatched == []
