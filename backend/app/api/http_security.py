"""Protections applied to every route: cross-site request rejection and security headers.

CSRF defence checks where a state-changing request comes from instead of issuing tokens, so the
frontend needs no extra header. Browsers mark requests with ``Sec-Fetch-Site`` and ``Origin``,
which a page on another site cannot forge; requests carrying neither are not from a browser and
cannot ride on its cookies. The session cookie's ``SameSite=Lax`` stays as a second layer.
"""

import json
import logging
from collections.abc import Iterable
from urllib.parse import urlsplit

from fastapi import FastAPI
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings

logger = logging.getLogger(__name__)

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
SAME_ORIGIN_FETCH_SITES = frozenset({"same-origin", "none"})
HSTS_VALUE = "max-age=31536000; includeSubDomains"
API_CSP = "default-src 'none'; frame-ancestors 'none'"
# The Swagger UI pages load scripts from a CDN; they only exist outside prod.
DOCS_PATHS = ("/docs", "/redoc")


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/").lower()


class CrossSiteRequestGuard:
    """Rejects unsafe-method requests that a browser sent from another origin.

    ``trusted_origins`` (the configured CORS origins) may call cross-origin, e.g. the dev frontend
    talking to the backend directly.
    """

    def __init__(self, app: ASGIApp, trusted_origins: Iterable[str]) -> None:
        self.app = app
        self.trusted_origins = frozenset(_normalize_origin(o) for o in trusted_origins)

    def _allowed(self, headers: Headers) -> bool:
        origin = headers.get("origin")
        if origin is not None and _normalize_origin(origin) in self.trusted_origins:
            return True
        fetch_site = headers.get("sec-fetch-site")
        if fetch_site is not None:
            return fetch_site.lower() in SAME_ORIGIN_FETCH_SITES
        if origin is None:
            return True
        # Older browsers send Origin without Sec-Fetch-Site. Behind the Next.js proxy the Host
        # header names the backend, so the proxy's X-Forwarded-Host is accepted as well.
        origin_host = urlsplit(origin.strip()).netloc.lower()
        hosts = {headers.get("host", ""), headers.get("x-forwarded-host", "")}
        return bool(origin_host) and origin_host in {h.strip().lower() for h in hosts if h}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in SAFE_METHODS:
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        if self._allowed(headers):
            await self.app(scope, receive, send)
            return
        logger.warning(
            "rejected cross-site %s %s sec-fetch-site=%s",
            scope["method"],
            scope["path"],
            headers.get("sec-fetch-site", "-"),
        )
        body = json.dumps(
            {"detail": {"code": "cross_site_request", "message": "Cross-site request rejected"}}
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


class SecurityHeaders:
    """Adds baseline security headers without overriding ones a route already set (the SSE
    stream sets its own ``Cache-Control``)."""

    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_docs = scope["path"].startswith(DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "no-referrer")
                headers.setdefault("Cache-Control", "no-store")
                if not is_docs:
                    headers.setdefault("Content-Security-Policy", API_CSP)
                if self.hsts:
                    headers.setdefault("Strict-Transport-Security", HSTS_VALUE)
            await send(message)

        await self.app(scope, receive, send_with_headers)


def install_http_security(app: FastAPI, settings: Settings) -> None:
    """Call before adding CORS so preflight answers stay outermost and the guard's 403 still
    carries the security headers."""
    app.add_middleware(CrossSiteRequestGuard, trusted_origins=settings.cors_origins)
    app.add_middleware(SecurityHeaders, hsts=settings.app_env == "prod")
