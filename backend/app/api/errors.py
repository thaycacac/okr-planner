from typing import Any

from fastapi import HTTPException

from app.api.schemas import ErrorResponse


class ApiError(HTTPException):
    """Serialized as ``ErrorResponse``: ``{"detail": {"code": ..., "message": ...}}``."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        attempts_left: int | None = None,
        retry_after_seconds: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        detail: dict[str, Any] = {"code": code, "message": message}
        if attempts_left is not None:
            detail["attempts_left"] = attempts_left
        if retry_after_seconds is not None:
            detail["retry_after_seconds"] = retry_after_seconds
        super().__init__(status_code=status_code, detail=detail, headers=headers)


def not_found(entity: str, entity_id: object) -> ApiError:
    return ApiError(404, "not_found", f"{entity} {entity_id} not found")


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    descriptions = {
        401: "Not signed in",
        404: "Not found",
        409: "Conflict with the current state",
        422: "Validation error",
        429: "Too many attempts",
        502: "The AI provider failed or returned unusable output",
    }
    return {
        code: {"model": ErrorResponse, "description": descriptions.get(code, "Error")}
        for code in status_codes
    }
