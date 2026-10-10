from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.api.security import SESSION_COOKIE
from app.config import Settings
from app.main import create_app
from tests.api_support import TEST_PASSWORD, ApiHarness, with_password

PROD_SECRET = "x" * 48
FRONTEND = "http://localhost:3000"


@contextmanager
def make_client(engine: Engine, **overrides: Any) -> Iterator[TestClient]:
    settings = with_password(Settings(database_url=str(engine.url), **overrides))
    with TestClient(create_app(settings, engine=engine)) as client:
        yield client


def put_calendar(api: ApiHarness, headers: dict[str, str]) -> Any:
    body = api.client.get("/settings/calendar").json()
    return api.client.put("/settings/calendar", json=body, headers=headers)


def assert_rejected(response: Any) -> None:
    assert response.status_code == 403
    assert response.json() == {
        "detail": {"code": "cross_site_request", "message": "Cross-site request rejected"}
    }


@pytest.mark.parametrize(
    "headers",
    [
        {"Sec-Fetch-Site": "cross-site", "Origin": "https://evil.example"},
        {"Sec-Fetch-Site": "same-site", "Origin": "https://evil.localhost"},
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
    ],
)
def test_cross_site_writes_are_rejected(api: ApiHarness, headers: dict[str, str]) -> None:
    assert_rejected(put_calendar(api, headers))


@pytest.mark.parametrize(
    "headers",
    [
        {"Sec-Fetch-Site": "same-origin", "Origin": "https://app.example"},
        {"Sec-Fetch-Site": "none"},
        {"Origin": "http://testserver"},
        # Behind the Next.js proxy the Host header names the backend.
        {"Origin": "https://app.example", "X-Forwarded-Host": "app.example"},
        {"Sec-Fetch-Site": "same-site", "Origin": FRONTEND},
        {},
    ],
)
def test_same_origin_trusted_and_non_browser_writes_pass(
    api: ApiHarness, headers: dict[str, str]
) -> None:
    assert put_calendar(api, headers).status_code == 200


def test_cross_site_reads_are_not_blocked(api: ApiHarness) -> None:
    response = api.client.get("/auth/me", headers={"Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 200


def test_cross_site_logout_keeps_the_session(api: ApiHarness) -> None:
    assert_rejected(api.client.post("/auth/logout", headers={"Sec-Fetch-Site": "cross-site"}))
    assert api.client.get("/auth/me").status_code == 200


def test_cross_site_login_is_rejected_before_checking_the_password(db_engine: Engine) -> None:
    with make_client(db_engine) as client:
        for _ in range(10):
            response = client.post(
                "/auth/login",
                json={"password": TEST_PASSWORD},
                headers={"Sec-Fetch-Site": "cross-site", "Origin": "https://evil.example"},
            )
            assert_rejected(response)
        assert SESSION_COOKIE not in client.cookies
        # Rejected requests do not use up the login budget.
        wrong = client.post("/auth/login", json={"password": "wrong"})
        assert wrong.json()["detail"]["attempts_left"] == 4


def test_security_headers_on_api_and_error_responses(api: ApiHarness) -> None:
    ok = api.client.get("/auth/me")
    rejected = api.client.post("/auth/logout", headers={"Sec-Fetch-Site": "cross-site"})
    for response in (ok, rejected):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["content-security-policy"] == (
            "default-src 'none'; frame-ancestors 'none'"
        )
        assert "strict-transport-security" not in response.headers


def test_docs_are_served_outside_prod_without_the_api_csp(api: ApiHarness) -> None:
    assert api.client.get("/openapi.json").status_code == 200
    docs = api.client.get("/docs")
    assert docs.status_code == 200
    assert "content-security-policy" not in docs.headers


def test_prod_sends_hsts_and_hides_the_schema(db_engine: Engine) -> None:
    with make_client(db_engine, app_env="prod", session_secret=PROD_SECRET) as client:
        health = client.get("/health")
        assert health.headers["strict-transport-security"] == (
            "max-age=31536000; includeSubDomains"
        )
        for path in ("/openapi.json", "/docs", "/redoc"):
            assert client.get(path).status_code == 404
