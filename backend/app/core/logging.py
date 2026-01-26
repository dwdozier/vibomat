"""
Structured logging module for Vibomat application.

This module provides JSON-formatted logging with request correlation and automatic
sanitization of sensitive fields like tokens, passwords, and API keys.

Usage:
    from backend.app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("User action", extra={"user_id": 123, "action": "login"})
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict, Mapping, Optional

from pythonjsonlogger.json import JsonFormatter


# Context variable to store request ID for correlation
REQUEST_ID_VAR: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Sensitive field names that should be redacted from logs (case-insensitive)
SENSITIVE_FIELDS = {
    "password",
    "access_token",
    "refresh_token",
    "api_key",
    "client_secret",
    "secret",
    "token",
    "authorization",
    "api_secret",
    "private_key",
}


class CustomJsonFormatter(JsonFormatter):
    """
    Custom JSON formatter that includes request_id and timestamps.

    This formatter extends python-json-logger to automatically include request IDs
    from context variables and format timestamps in a consistent way.
    """

    def add_fields(self, log_data: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add custom fields to the log record.

        Args:
            log_data: Dictionary to be logged as JSON
            record: Python LogRecord object
            message_dict: Dictionary of message-specific fields
        """
        super().add_fields(log_data, record, message_dict)

        # Add timestamp
        if not log_data.get("timestamp"):
            log_data["timestamp"] = self.formatTime(record, self.datefmt)

        # Add log level
        if log_data.get("level"):
            log_data["level"] = log_data["level"].upper()
        else:
            log_data["level"] = record.levelname

        # Add request ID from context if available
        try:
            request_id = REQUEST_ID_VAR.get()
            if request_id:
                log_data["request_id"] = request_id
        except LookupError:
            # No request ID in context, that's fine
            pass


class StructuredLogger(logging.Logger):
    """
    Logger class that automatically sanitizes sensitive data.

    This logger extends Python's logging.Logger to automatically sanitize sensitive
    fields before logging. Use get_logger() to obtain instances of this class.
    """

    def _log(  # type: ignore[override]
        self,
        level: int,
        msg: object,
        args: tuple,
        exc_info: Any = None,
        extra: Optional[Mapping[str, object]] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """
        Override _log to sanitize extra data before logging.

        Args:
            level: Log level (DEBUG, INFO, etc.)
            msg: Log message
            args: Message format arguments
            exc_info: Exception information
            extra: Extra fields to include in log
            stack_info: Whether to include stack trace
            stacklevel: Stack level for caller info
        """
        # Sanitize extra data if present
        sanitized_extra: Optional[Mapping[str, object]] = None
        if extra:
            sanitized_extra = sanitize_log_data(dict(extra))

        super()._log(
            level, msg, args, exc_info=exc_info, extra=sanitized_extra, stack_info=stack_info, stacklevel=stacklevel
        )


def sanitize_log_data(data: Any) -> Any:
    """
    Recursively sanitize sensitive fields in data structures.

    This function walks through dictionaries and lists, redacting values for any keys
    that match sensitive field names (case-insensitive).

    Args:
        data: Data to sanitize (dict, list, or other type)

    Returns:
        Sanitized copy of the data with sensitive fields redacted
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key is sensitive (case-insensitive)
            if isinstance(key, str) and key.lower() in SENSITIVE_FIELDS:
                sanitized[key] = "[REDACTED]"
            else:
                # Recursively sanitize nested structures
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_log_data(item) for item in data)
    else:
        # Primitive types, return as-is
        return data


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a structured logger instance with JSON formatting.

    This function returns a logger configured with JSON formatting and automatic
    sanitization of sensitive fields. All loggers use the StructuredLogger class.

    Args:
        name: Logger name (typically __name__)
        level: Log level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Set the custom logger class
    logging.setLoggerClass(StructuredLogger)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handler if logger doesn't have one
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def set_request_id(request_id: str) -> None:
    """
    Set the request ID for the current context.

    This function should be called at the beginning of request processing to enable
    request correlation across all log messages.

    Args:
        request_id: Unique identifier for the request
    """
    REQUEST_ID_VAR.set(request_id)


def clear_request_id() -> None:
    """
    Clear the request ID from the current context.

    This function should be called at the end of request processing.
    """
    try:
        REQUEST_ID_VAR.set(None)
    except LookupError:
        pass
