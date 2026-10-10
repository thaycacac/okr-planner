import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.api.security import SESSION_COOKIE, AuthState, LoginRateLimiter, SessionStore
from app.config import Settings
from app.main import create_app
from tests.api_support import TEST_PASSWORD, FakeClock, with_password

PROD_SECRET = "x" * 48
PROXY = "10.0.0.2"


@contextmanager
def make_client(
    engine: Engine, *, peer: str = "198.51.100.1", **overrides: Any
) -> Iterator[TestClient]:
    settings = with_password(Settings(database_url=str(engine.url), **overrides))
    with TestClient(create_app(settings, engine=engine), client=(peer, 50000)) as client:
        yield client


def login(client: TestClient, password: str = TEST_PASSWORD, **kwargs: Any) -> Any:
    return client.post("/auth/login", json={"password": password}, **kwargs)


@pytest.fixture
def client(db_engine: Engine) -> Iterator[TestClient]:
    with make_client(db_engine) as client:
        yield client


PROTECTED = [
    ("get", "/auth/me"),
    ("get", "/settings/calendar"),
    ("get", "/settings/llm"),
    ("get", "/quarters/1"),
    ("post", "/plans"),
    ("get", "/plans/abc/events"),
]


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_api_requires_a_session(client: TestClient, method: str, path: str) -> None:
    response = client.request(method, path, json={})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "not_authenticated"


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_probes_stay_public(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 200


def test_wrong_password_is_rejected_with_attempts_left(client: TestClient) -> None:
    response = login(client, "wrong")
    assert response.status_code == 401
    assert response.json()["detail"] == {
        "code": "invalid_password",
        "message": "Wrong password",
        "attempts_left": 4,
    }
    assert SESSION_COOKIE not in response.cookies
    assert client.get("/auth/me").status_code == 401


def test_login_grants_access_and_logout_revokes_it(client: TestClient) -> None:
    response = login(client)
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    token = client.cookies[SESSION_COOKIE]

    assert client.get("/auth/me").json() == {"authenticated": True}
    assert client.get("/settings/calendar").status_code == 200

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401
    assert client.get("/settings/calendar").status_code == 401

    # A copy of the cookie kept after logout is no longer accepted either.
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/auth/me").status_code == 401


def test_logout_without_session_succeeds(client: TestClient) -> None:
    assert client.post("/auth/logout").status_code == 204


def test_tampered_cookie_is_rejected(client: TestClient) -> None:
    login(client)
    session_id, expires, signature = client.cookies[SESSION_COOKIE].split(".")
    client.cookies.set(SESSION_COOKIE, f"{session_id}.{int(expires) + 3600}.{signature}")
    assert client.get("/auth/me").status_code == 401


def auth_state(client: TestClient) -> AuthState:
    state: AuthState = client.app.state.context.auth  # type: ignore[attr-defined]
    return state


def test_session_expires_after_max_age(client: TestClient) -> None:
    clock = FakeClock()
    auth_state(client).sessions = SessionStore("secret", max_age_seconds=3600, clock=clock)
    login(client)
    clock.now += 3599
    assert client.get("/auth/me").status_code == 200
    clock.now += 1
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "not_authenticated"


def test_rotating_session_secret_signs_everyone_out(db_engine: Engine) -> None:
    with make_client(db_engine, session_secret="a" * 48) as old:
        login(old)
        token = old.cookies[SESSION_COOKIE]
    with make_client(db_engine, session_secret="b" * 48) as new:
        new.cookies.set(SESSION_COOKIE, token)
        assert new.get("/auth/me").status_code == 401
        assert new.get("/settings/calendar").status_code == 401


def test_repeated_lockouts_back_off(client: TestClient) -> None:
    clock = FakeClock()
    auth_state(client).limiter = LoginRateLimiter(
        max_attempts=2, lock_seconds=60, max_lock_seconds=900, clock=clock
    )
    for expected in (60, 120, 240):
        login(client, "wrong")
        locked = login(client, "wrong")
        assert locked.status_code == 429
        assert locked.json()["detail"]["retry_after_seconds"] == expected
        assert locked.headers["retry-after"] == str(expected)
        clock.now += expected - 1
        assert login(client).status_code == 429
        clock.now += 1
    assert login(client).status_code == 200


def test_session_cookie_attributes_in_dev(client: TestClient) -> None:
    cookie = login(client).headers["set-cookie"].lower()
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age=604800" in cookie
    assert "domain" not in cookie
    assert "secure" not in cookie


def test_session_cookie_is_secure_in_prod_even_over_http(db_engine: Engine) -> None:
    with make_client(db_engine, app_env="prod", session_secret=PROD_SECRET) as client:
        cookie = login(client).headers["set-cookie"].lower()
        logout_cookie = client.post("/auth/logout").headers["set-cookie"].lower()
    assert "; secure" in cookie
    assert "domain" not in cookie
    assert "; secure" in logout_cookie
    assert "max-age=0" in logout_cookie


def test_login_locks_after_max_failures(client: TestClient) -> None:
    for left in (4, 3, 2, 1):
        assert login(client, "wrong").json()["detail"]["attempts_left"] == left
    locked = login(client, "wrong")
    assert locked.status_code == 429
    assert locked.json()["detail"]["code"] == "rate_limited"
    assert locked.json()["detail"]["retry_after_seconds"] == 60
    assert locked.headers["retry-after"] == "60"
    # Even the right password waits out the lock.
    assert login(client).status_code == 429


def test_successful_login_resets_the_failure_count(client: TestClient) -> None:
    for _ in range(4):
        login(client, "wrong")
    assert login(client).status_code == 200
    assert login(client, "wrong").json()["detail"]["attempts_left"] == 4


def test_clients_behind_the_trusted_proxy_do_not_lock_each_other(db_engine: Engine) -> None:
    with make_client(db_engine, peer=PROXY, trusted_proxy_ips=["10.0.0.0/24"]) as client:
        for _ in range(5):
            login(client, "wrong", headers={"X-Forwarded-For": "203.0.113.5"})
        assert login(client, headers={"X-Forwarded-For": "203.0.113.5"}).status_code == 429

        other = login(client, "wrong", headers={"X-Forwarded-For": "203.0.113.9"})
        assert other.status_code == 401
        assert other.json()["detail"]["attempts_left"] == 4
        assert login(client, headers={"X-Forwarded-For": "203.0.113.9"}).status_code == 200


def test_spoofed_hops_before_the_proxy_entry_are_ignored(db_engine: Engine) -> None:
    with make_client(db_engine, peer=PROXY, trusted_proxy_ips=[PROXY]) as client:
        for n in range(5):
            login(client, "wrong", headers={"X-Forwarded-For": f"1.1.1.{n}, 203.0.113.5"})
        response = login(client, headers={"X-Forwarded-For": "1.1.1.99, 203.0.113.5"})
    assert response.status_code == 429


def test_forwarded_for_from_an_untrusted_peer_is_ignored(db_engine: Engine) -> None:
    with make_client(db_engine, peer="198.51.100.7", trusted_proxy_ips=[PROXY]) as client:
        for n in range(5):
            login(client, "wrong", headers={"X-Forwarded-For": f"203.0.113.{n}"})
        response = login(client, headers={"X-Forwarded-For": "203.0.113.200"})
    assert response.status_code == 429


def test_forwarded_for_is_ignored_without_trusted_proxies(db_engine: Engine) -> None:
    with make_client(db_engine, peer=PROXY) as client:
        for n in range(5):
            login(client, "wrong", headers={"X-Forwarded-For": f"203.0.113.{n}"})
        assert login(client, headers={"X-Forwarded-For": "203.0.113.200"}).status_code == 429


def test_single_value_client_ip_header(db_engine: Engine) -> None:
    with make_client(
        db_engine, peer=PROXY, trusted_proxy_ips=[PROXY], client_ip_header="X-Real-IP"
    ) as client:
        for _ in range(5):
            login(client, "wrong", headers={"X-Real-IP": "203.0.113.5"})
        assert login(client, headers={"X-Real-IP": "203.0.113.5"}).status_code == 429
        assert login(client, headers={"X-Real-IP": "203.0.113.9"}).status_code == 200


def test_login_without_configured_hash_is_unavailable(db_engine: Engine) -> None:
    settings = Settings(database_url=str(db_engine.url))
    with TestClient(create_app(settings, engine=db_engine)) as client:
        response = login(client)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "auth_not_configured"


def test_login_body_is_validated(client: TestClient) -> None:
    assert client.post("/auth/login", json={"password": ""}).status_code == 422
    assert client.post("/auth/login", json={"password": "x", "extra": 1}).status_code == 422


def test_password_and_cookie_never_reach_the_logs(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    login(client, "hunter2-wrong")
    login(client)
    token = client.cookies[SESSION_COOKIE]
    client.post("/auth/logout")
    assert "login failed" in caplog.text
    for secret in ("hunter2-wrong", TEST_PASSWORD, token):
        assert secret not in caplog.text
