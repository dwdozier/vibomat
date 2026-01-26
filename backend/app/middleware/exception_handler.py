"""
Global exception handler middleware for FastAPI.

This module provides exception handlers that map custom exceptions to appropriate
HTTP responses, log errors, and sanitize error messages before sending them to clients.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from backend.app.exceptions import ViboMatException

# Get logger for this module
logger = logging.getLogger(__name__)


async def vibomat_exception_handler(request: Request, exc: ViboMatException) -> JSONResponse:  # type: ignore[return]
    """
    Handle all ViboMatException and its subclasses.

    This handler maps custom exceptions to HTTP responses with appropriate status codes.
    It logs the full exception details internally while returning sanitized messages to
    clients.

    Args:
        request: The FastAPI request object
        exc: The ViboMatException that was raised

    Returns:
        JSONResponse with error details
    """
    # Log the exception with full details
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "exception_type": exc.__class__.__name__,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Determine status code (use exception's status_code or default to 500)
    status_code = exc.status_code if exc.status_code else 500

    # Return sanitized error message to client
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )


async def validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:  # type: ignore[return]
    """
    Handle Pydantic validation errors.

    This handler catches validation errors from Pydantic models and returns them in a
    consistent format.

    Args:
        request: The FastAPI request object
        exc: The Pydantic ValidationError that was raised

    Returns:
        JSONResponse with validation error details
    """
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[return]
    """
    Handle all uncaught exceptions.

    This is the fallback handler for any exceptions that are not caught by more specific
    handlers. It logs the full exception and returns a generic error message to prevent
    information leakage.

    Args:
        request: The FastAPI request object
        exc: The generic Exception that was raised

    Returns:
        JSONResponse with generic error message
    """
    # Log the exception with full details for debugging
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Return generic error message to prevent information leakage
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
