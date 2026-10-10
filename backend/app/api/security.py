"""Shared-password auth: signed session tokens, login rate limiting and client IP resolution.

State lives in process memory, matching the single-process deployment (see ADR 0001): a restart
forgets revoked sessions and failed attempts, but not the signing secret.
"""

import base64
import hashlib
import hmac
import ipaddress
import logging
import math
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass

from argon2 import PasswordHasher, extract_parameters
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.requests import Request

from app.config import DEV_SESSION_SECRET, Settings

logger = logging.getLogger(__name__)

SESSION_COOKIE = "okr_session"
MIN_PROD_SECRET_LENGTH = 32

Clock = Callable[[], float]
IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False
    except InvalidHashError:
        logger.error("APP_PASSWORD_HASH is not a valid argon2 hash")
        return False


def check_auth_settings(settings: Settings) -> None:
    """Fail at startup instead of serving an API that nobody (or anybody) can log in to."""
    password_hash = settings.app_password_hash
    if password_hash is not None:
        try:
            extract_parameters(password_hash.get_secret_value())
        except InvalidHashError as exc:
            raise ValueError("APP_PASSWORD_HASH is not a valid argon2 hash") from exc
    if settings.app_env != "prod":
        if password_hash is None:
            logger.warning("APP_PASSWORD_HASH is not set: every login will be refused")
        return
    if password_hash is None:
        raise ValueError("APP_PASSWORD_HASH must be set when APP_ENV=prod")
    secret = settings.session_secret.get_secret_value()
    if secret == DEV_SESSION_SECRET or len(secret) < MIN_PROD_SECRET_LENGTH:
        raise ValueError(
            f"SESSION_SECRET must be a random value of at least {MIN_PROD_SECRET_LENGTH} "
            "characters when APP_ENV=prod"
        )


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


class SessionStore:
    """Tokens are ``<session id>.<expiry epoch>.<HMAC-SHA256>``; logout revokes the session id.

    Rotating the secret invalidates every issued token, and lowering ``max_age_seconds`` also
    shortens sessions issued before the change."""

    def __init__(self, secret: str, max_age_seconds: int, clock: Clock = time.time) -> None:
        self._key = secret.encode("utf-8")
        self.max_age_seconds = max_age_seconds
        self._clock = clock
        self._revoked: dict[str, int] = {}

    def _sign(self, payload: str) -> str:
        return _b64(hmac.new(self._key, payload.encode("ascii"), hashlib.sha256).digest())

    def issue(self) -> str:
        payload = f"{secrets.token_urlsafe(24)}.{int(self._clock()) + self.max_age_seconds}"
        return f"{payload}.{self._sign(payload)}"

    def _parse(self, token: str | None) -> tuple[str, int] | None:
        if not token or not token.isascii():
            return None
        parts = token.split(".")
        if len(parts) != 3:
            return None
        session_id, expires, signature = parts
        if not hmac.compare_digest(signature, self._sign(f"{session_id}.{expires}")):
            return None
        if not expires.isdigit():
            return None
        now = self._clock()
        if not now < int(expires) <= now + self.max_age_seconds:
            return None
        return session_id, int(expires)

    def is_valid(self, token: str | None) -> bool:
        parsed = self._parse(token)
        return parsed is not None and parsed[0] not in self._revoked

    def revoke(self, token: str | None) -> None:
        parsed = self._parse(token)
        if parsed is None:
            return
        now = self._clock()
        self._revoked = {sid: exp for sid, exp in self._revoked.items() if exp > now}
        self._revoked[parsed[0]] = parsed[1]


@dataclass
class _Attempts:
    started_at: float
    count: int = 0
    locked_until: float = 0.0
    locks: int = 0


class LoginRateLimiter:
    """Allows ``max_attempts`` failed logins per client within ``window_seconds``; the next one
    locks the client. Each lock lasts twice as long as the previous one, from ``lock_seconds`` up
    to ``max_lock_seconds``, until the client succeeds or stays quiet for ``window_seconds``.
    Attempts are counted before the password is checked, so parallel requests cannot run more
    verifications than allowed."""

    def __init__(
        self,
        max_attempts: int,
        lock_seconds: int,
        *,
        max_lock_seconds: int = 15 * 60,
        window_seconds: int = 15 * 60,
        max_clients: int = 10_000,
        clock: Clock = time.monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.lock_seconds = lock_seconds
        self.max_lock_seconds = max(lock_seconds, max_lock_seconds)
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._clock = clock
        self._clients: dict[str, _Attempts] = {}

    def _retry_after(self, entry: _Attempts, now: float) -> int:
        return max(1, math.ceil(entry.locked_until - now))

    def _stale(self, entry: _Attempts, now: float) -> bool:
        return now - max(entry.started_at, entry.locked_until) >= self.window_seconds

    def _lock(self, entry: _Attempts, now: float) -> int:
        entry.locks += 1
        doublings = min(entry.locks - 1, 32)
        entry.locked_until = now + min(self.lock_seconds * 2**doublings, self.max_lock_seconds)
        entry.count = 0
        entry.started_at = now
        return self._retry_after(entry, now)

    def _entry(self, client: str, now: float) -> _Attempts:
        entry = self._clients.get(client)
        if entry is not None and not self._stale(entry, now):
            return entry
        if len(self._clients) >= self.max_clients:
            self._clients = {k: v for k, v in self._clients.items() if not self._stale(v, now)}
            while len(self._clients) >= self.max_clients:
                self._clients.pop(next(iter(self._clients)))
        entry = self._clients[client] = _Attempts(started_at=now)
        return entry

    def reserve(self, client: str) -> int | None:
        """Seconds until the client may retry, or ``None`` if it may check a password now."""
        now = self._clock()
        entry = self._entry(client, now)
        if entry.locked_until > now:
            return self._retry_after(entry, now)
        if entry.count >= self.max_attempts:
            return self._lock(entry, now)
        entry.count += 1
        return None

    def failed(self, client: str) -> int | None:
        """Seconds until the client may retry if it is now locked, else ``None``."""
        now = self._clock()
        entry = self._entry(client, now)
        if entry.locked_until > now:
            return self._retry_after(entry, now)
        if entry.count < self.max_attempts:
            return None
        return self._lock(entry, now)

    def attempts_left(self, client: str) -> int:
        entry = self._clients.get(client)
        return self.max_attempts - (entry.count if entry else 0)

    def succeeded(self, client: str) -> None:
        self._clients.pop(client, None)


def _parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    value = value.strip()
    if value.startswith("[") and "]" in value:
        value = value[1 : value.index("]")]
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


@dataclass
class ClientIpResolver:
    """Reads the client IP from a proxy header only when the peer is a trusted proxy, so a
    header sent straight to the backend cannot pick its own rate-limit bucket."""

    trusted: list[IPNetwork]
    header: str = "x-forwarded-for"

    @classmethod
    def from_settings(cls, settings: Settings) -> "ClientIpResolver":
        return cls(
            trusted=[ipaddress.ip_network(value) for value in settings.trusted_proxy_ips],
            header=settings.client_ip_header,
        )

    def _is_trusted(self, value: str) -> bool:
        ip = _parse_ip(value)
        return ip is not None and any(ip in network for network in self.trusted)

    def resolve(self, request: Request) -> str:
        peer = request.client.host if request.client else "unknown"
        if not self.trusted or not self._is_trusted(peer):
            return peer
        values = request.headers.getlist(self.header)
        if self.header != "x-forwarded-for":
            ip = _parse_ip(values[-1]) if values else None
            return str(ip) if ip is not None else peer
        hops = [hop.strip() for value in values for hop in value.split(",") if hop.strip()]
        for hop in reversed(hops):
            if not self._is_trusted(hop):
                ip = _parse_ip(hop)
                # Only the entry appended by our proxy is trustworthy; garbage there means the
                # chain is broken, so fall back to the proxy itself rather than guess.
                return str(ip) if ip is not None else peer
        return peer


@dataclass
class AuthState:
    sessions: SessionStore
    limiter: LoginRateLimiter
    client_ip: ClientIpResolver
    secure_cookie: bool = False

    @classmethod
    def from_settings(cls, settings: Settings) -> "AuthState":
        return cls(
            sessions=SessionStore(
                settings.session_secret.get_secret_value(),
                settings.session_max_age_hours * 3600,
            ),
            limiter=LoginRateLimiter(
                settings.login_max_attempts,
                settings.login_lock_seconds,
                max_lock_seconds=settings.login_lock_max_seconds,
            ),
            client_ip=ClientIpResolver.from_settings(settings),
            secure_cookie=settings.app_env == "prod",
        )
