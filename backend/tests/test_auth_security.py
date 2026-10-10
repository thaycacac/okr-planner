import io
import sys

import pytest
from pydantic import SecretStr, ValidationError

from app import hash_password as cli
from app.api.security import (
    LoginRateLimiter,
    SessionStore,
    check_auth_settings,
    verify_password,
)
from app.config import Settings
from tests.api_support import TEST_PASSWORD, TEST_PASSWORD_HASH, FakeClock


def test_session_expires_after_max_age() -> None:
    clock = FakeClock()
    store = SessionStore("secret", max_age_seconds=60, clock=clock)
    token = store.issue()
    clock.now += 59
    assert store.is_valid(token)
    clock.now += 1
    assert not store.is_valid(token)


def test_session_signed_with_another_secret_is_rejected() -> None:
    token = SessionStore("secret-a", 60).issue()
    assert not SessionStore("secret-b", 60).is_valid(token)


@pytest.mark.parametrize("token", [None, "", "a.b", "a.b.c.d", "ü.1.x", "abc.notanumber.sig"])
def test_malformed_tokens_are_rejected(token: str | None) -> None:
    store = SessionStore("secret", 60)
    assert not store.is_valid(token)
    store.revoke(token)


def test_lowering_max_age_shortens_sessions_already_issued() -> None:
    clock = FakeClock()
    token = SessionStore("secret", max_age_seconds=3600, clock=clock).issue()
    assert not SessionStore("secret", max_age_seconds=60, clock=clock).is_valid(token)
    assert SessionStore("secret", max_age_seconds=7200, clock=clock).is_valid(token)


def test_revoked_sessions_are_pruned_once_expired() -> None:
    clock = FakeClock()
    store = SessionStore("secret", max_age_seconds=60, clock=clock)
    first = store.issue()
    store.revoke(first)
    clock.now += 61
    store.revoke(store.issue())
    assert len(store._revoked) == 1


def test_lock_expires_and_grants_a_fresh_budget() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=2, lock_seconds=30, clock=clock)
    for _ in range(2):
        assert limiter.reserve("a") is None
    assert limiter.failed("a") == 30
    clock.now += 29.5
    assert limiter.reserve("a") == 1
    clock.now += 0.5
    assert limiter.reserve("a") is None
    assert limiter.attempts_left("a") == 1


def test_parallel_attempts_cannot_exceed_the_budget() -> None:
    limiter = LoginRateLimiter(max_attempts=3, lock_seconds=30, clock=FakeClock())
    results = [limiter.reserve("a") for _ in range(5)]
    assert results[:3] == [None, None, None]
    assert results[3:] == [30, 30]


def _fail_until_locked(limiter: LoginRateLimiter, client: str = "a") -> int | None:
    for _ in range(limiter.max_attempts):
        assert limiter.reserve(client) is None
    return limiter.failed(client)


def test_repeated_locks_back_off_exponentially_up_to_the_cap() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=2, lock_seconds=30, max_lock_seconds=100, clock=clock)
    for expected in (30, 60, 100, 100):
        assert _fail_until_locked(limiter) == expected
        clock.now += expected
    assert limiter.reserve("b") is None


def test_backoff_resets_after_a_quiet_window() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=2, lock_seconds=30, window_seconds=600, clock=clock)
    assert _fail_until_locked(limiter) == 30
    clock.now += 30 + 599
    assert _fail_until_locked(limiter) == 60
    clock.now += 60 + 600
    assert _fail_until_locked(limiter) == 30


def test_backoff_resets_after_a_successful_login() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=2, lock_seconds=30, clock=clock)
    assert _fail_until_locked(limiter) == 30
    clock.now += 30
    limiter.reserve("a")
    limiter.succeeded("a")
    assert _fail_until_locked(limiter) == 30


def test_failures_finishing_during_a_lock_report_the_lock() -> None:
    limiter = LoginRateLimiter(max_attempts=2, lock_seconds=30, clock=FakeClock())
    assert limiter.reserve("a") is None
    assert limiter.reserve("a") is None
    assert limiter.reserve("a") == 30
    assert limiter.failed("a") == 30
    assert limiter.failed("a") == 30


def test_failures_are_forgotten_after_the_window() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=3, lock_seconds=30, window_seconds=600, clock=clock)
    limiter.reserve("a")
    limiter.failed("a")
    clock.now += 600
    limiter.reserve("a")
    assert limiter.attempts_left("a") == 2


def test_tracked_clients_are_bounded() -> None:
    limiter = LoginRateLimiter(max_attempts=3, lock_seconds=30, max_clients=100, clock=FakeClock())
    for n in range(250):
        limiter.reserve(f"client-{n}")
    assert len(limiter._clients) <= 100


def test_verify_password() -> None:
    assert verify_password(TEST_PASSWORD_HASH, TEST_PASSWORD)
    assert not verify_password(TEST_PASSWORD_HASH, "nope")
    assert not verify_password("not-a-hash", TEST_PASSWORD)


def test_prod_requires_a_password_hash() -> None:
    with pytest.raises(ValueError, match="APP_PASSWORD_HASH"):
        check_auth_settings(Settings(app_env="prod", session_secret=SecretStr("x" * 48)))


@pytest.mark.parametrize("secret", ["dev-only-change-me", "too-short"])
def test_prod_requires_a_strong_session_secret(secret: str) -> None:
    settings = Settings(
        app_env="prod",
        app_password_hash=SecretStr(TEST_PASSWORD_HASH),
        session_secret=SecretStr(secret),
    )
    with pytest.raises(ValueError, match="SESSION_SECRET"):
        check_auth_settings(settings)


def test_invalid_hash_fails_at_startup() -> None:
    with pytest.raises(ValueError, match="argon2"):
        check_auth_settings(Settings(app_password_hash=SecretStr("plaintext")))


def test_blank_hash_counts_as_unset() -> None:
    assert Settings(app_password_hash="  ").app_password_hash is None  # type: ignore[arg-type]


def test_trusted_proxies_must_be_ip_networks() -> None:
    assert Settings(trusted_proxy_ips=["10.0.0.0/8", "fd12::/16", "127.0.0.1"])
    with pytest.raises(ValidationError):
        Settings(trusted_proxy_ips=["*"])


def test_cli_hashes_the_password_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("s3cret-pass\n"))
    cli.main()
    printed = capsys.readouterr().out.strip()
    assert printed.startswith("$argon2id$")
    assert verify_password(printed, "s3cret-pass")


def test_cli_rejects_an_empty_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))
    with pytest.raises(SystemExit):
        cli.main()
