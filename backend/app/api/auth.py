import logging

from fastapi import APIRouter, Depends, Request, Response, status
from starlette.concurrency import run_in_threadpool

from app.api.deps import Ctx, require_session
from app.api.errors import ApiError, error_responses
from app.api.schemas import ErrorResponse, LoginRequest, SessionInfo
from app.api.security import SESSION_COOKIE, AuthState, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _rate_limited(retry_after: int) -> ApiError:
    return ApiError(
        429,
        "rate_limited",
        "Too many attempts",
        retry_after_seconds=retry_after,
        headers={"Retry-After": str(retry_after)},
    )


def _set_session_cookie(response: Response, auth: AuthState, token: str) -> None:
    # Host-only (no Domain): behind the Next.js proxy the cookie belongs to the frontend host.
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=auth.sessions.max_age_seconds,
        path="/",
        secure=auth.secure_cookie,
        httponly=True,
        samesite="lax",
    )


@router.post(
    "/login",
    summary="Sign in with the shared password",
    responses={
        200: {"description": "Session cookie set"},
        401: {"model": ErrorResponse, "description": "Wrong password"},
        429: {"model": ErrorResponse, "description": "Too many attempts"},
        503: {"model": ErrorResponse, "description": "APP_PASSWORD_HASH is not configured"},
    },
)
async def login(body: LoginRequest, request: Request, response: Response, ctx: Ctx) -> SessionInfo:
    password_hash = ctx.settings.app_password_hash
    if password_hash is None:
        raise ApiError(503, "auth_not_configured", "Login is not configured on the server")
    auth = ctx.auth
    client = auth.client_ip.resolve(request)
    retry_after = auth.limiter.reserve(client)
    if retry_after is not None:
        raise _rate_limited(retry_after)

    if await run_in_threadpool(verify_password, password_hash.get_secret_value(), body.password):
        auth.limiter.succeeded(client)
        _set_session_cookie(response, auth, auth.sessions.issue())
        logger.info("login succeeded for client %s", client)
        return SessionInfo(authenticated=True)

    retry_after = auth.limiter.failed(client)
    if retry_after is not None:
        logger.warning("login locked for client %s for %ds", client, retry_after)
        raise _rate_limited(retry_after)
    attempts_left = auth.limiter.attempts_left(client)
    logger.warning("login failed for client %s, %d attempts left", client, attempts_left)
    raise ApiError(401, "invalid_password", "Wrong password", attempts_left=attempts_left)


@router.post(
    "/logout",
    summary="Clear the session cookie",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={204: {"description": "Signed out"}},
)
def logout(request: Request, ctx: Ctx) -> Response:
    """Always succeeds, so a client with an expired session can still clear its cookie."""
    ctx.auth.sessions.revoke(request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        SESSION_COOKIE, path="/", secure=ctx.auth.secure_cookie, httponly=True, samesite="lax"
    )
    return response


@router.get(
    "/me",
    summary="Current session",
    dependencies=[Depends(require_session)],
    responses={200: {"description": "Signed in"}, **error_responses(401)},
)
def me() -> SessionInfo:
    return SessionInfo(authenticated=True)
