"""
Sorim.AI — Centralized Error Handling

Implements the uniform error envelope defined in API_CONTRACTS.md §0:
    {"error": {"code": str, "message": str, "details": object|null}}

Error codes are from API_CONTRACTS.md §12.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ── Error envelope schema ────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Application error codes (from API_CONTRACTS.md §12) ─────────────────────

class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMPLOYEE_NOT_FOUND = "EMPLOYEE_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    SOFTWARE_NOT_IN_CATALOGUE = "SOFTWARE_NOT_IN_CATALOGUE"
    LLM_OUTPUT_INVALID = "LLM_OUTPUT_INVALID"
    SERVICENOW_UNAVAILABLE = "SERVICENOW_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    RETRIEVAL_UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ── Custom application exception ─────────────────────────────────────────────

class AppError(Exception):
    """Raise this in service/repository code to produce a structured API error."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details


def _make_error_response(
    code: str,
    message: str,
    details: Optional[Any] = None,
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"error": {"code": code, "message": message, "details": details}},
    )


# ── Exception handlers ───────────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _make_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        http_status=exc.http_status,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert FastAPI's default 422 body into the project error envelope."""
    details: dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []) if l != "body")
        details[loc or "request"] = err.get("msg", "invalid value")

    return _make_error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        details=details,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.
    Returns a safe generic message — never a stack trace to the client.
    The exception is logged server-side.
    """
    import logging

    logger = logging.getLogger("sorim.errors")
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _make_error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred. Please try again or contact support.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application instance."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]
