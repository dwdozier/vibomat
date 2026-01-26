"""
Error message sanitization for preventing information leakage.

This module provides functions to sanitize error messages and data structures before
they are sent to clients or logged, preventing exposure of sensitive information like
tokens, passwords, API keys, and connection strings.

Usage:
    from backend.app.core.error_sanitizer import sanitize_error_message

    error_msg = "Failed with token: abc123"
    safe_msg = sanitize_error_message(error_msg)
    # Returns: "Failed with token: [REDACTED_TOKEN]"
"""

import re
from typing import Any, Dict, Optional

# Sensitive field names that should be redacted in dictionaries (case-insensitive)
SENSITIVE_FIELD_NAMES = {
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
    "secret_key",
    "api_token",
    "auth_token",
    "bearer_token",
}

# Regex patterns for sensitive data in error messages
# Ordered from most specific to least specific to avoid false positives
SENSITIVE_PATTERNS = [
    {
        "pattern": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
        "replacement": "[REDACTED_TOKEN]",
        "description": "JWT tokens",
    },
    {
        "pattern": r"Bearer\s+[A-Za-z0-9_\-\.]+",
        "replacement": "[REDACTED_BEARER_TOKEN]",
        "description": "Bearer tokens",
    },
    {
        "pattern": r"(?:postgresql|mysql|mongodb)://[^:]+:[^@]+@[^\s]+",
        "replacement": "[REDACTED_CONNECTION_STRING]",
        "description": "Database connection strings with credentials",
    },
    {
        "pattern": r"redis://:[^@]+@[^\s]+",
        "replacement": "[REDACTED_CONNECTION_STRING]",
        "description": "Redis URLs with password",
    },
    {
        "pattern": r"(?:api[_-]?key|apikey)[=:\s]+(?:sk-)?[A-Za-z0-9_\-]{8,}",
        "replacement": r"api_key=[REDACTED_KEY]",
        "description": "API keys",
    },
    {
        "pattern": r"(?:password|passwd|pwd)[=:\s]+[^\s,;)]+",
        "replacement": r"password=[REDACTED_PASSWORD]",
        "description": "Passwords",
    },
    {
        "pattern": r"(?:client[_-]?secret|clientSecret)[=:\s]+[A-Za-z0-9]{16,}",
        "replacement": r"client_secret=[REDACTED_SECRET]",
        "description": "Client secrets",
    },
    {
        "pattern": r"(?:access[_-]?token|accessToken)[=:\s]+[A-Za-z0-9_\-\.]{6,}",
        "replacement": r"access_token=[REDACTED_TOKEN]",
        "description": "Access tokens",
    },
    {
        "pattern": r"(?:refresh[_-]?token|refreshToken)[=:\s]+[A-Za-z0-9_\-\.]{6,}",
        "replacement": r"refresh_token=[REDACTED_TOKEN]",
        "description": "Refresh tokens",
    },
    {
        "pattern": r"(?:token)[=:\s]+[A-Za-z0-9_\-\.]{6,}",
        "replacement": r"token=[REDACTED_TOKEN]",
        "description": "Generic tokens",
    },
    {
        "pattern": r"(?:Authorization|authorization):\s*[^\s]+",
        "replacement": r"Authorization: [REDACTED_AUTH]",
        "description": "Authorization headers",
    },
    {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "replacement": "[REDACTED_EMAIL]",
        "description": "Email addresses",
    },
    {
        "pattern": r"\b[0-9a-fA-F]{32,}\b",
        "replacement": "[REDACTED_HASH]",
        "description": "Long hexadecimal strings (likely secrets/hashes)",
    },
]


def sanitize_error_message(message: Optional[str]) -> str:
    """
    Sanitize an error message by redacting sensitive information.

    This function applies regex patterns to identify and redact common sensitive
    data patterns like tokens, passwords, API keys, emails, and connection strings.

    Args:
        message: Error message to sanitize

    Returns:
        Sanitized error message with sensitive data redacted
    """
    if not message:
        return ""

    sanitized = str(message)

    # Apply each pattern to redact sensitive information
    for pattern_info in SENSITIVE_PATTERNS:
        pattern = pattern_info["pattern"]
        replacement = pattern_info["replacement"]
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


def sanitize_dict(data: Any) -> Any:
    """
    Recursively sanitize a dictionary by redacting sensitive field values.

    This function walks through dictionaries and lists, redacting values for any keys
    that match sensitive field names (case-insensitive). It also sanitizes string
    values that might contain sensitive patterns.

    Args:
        data: Data structure to sanitize (dict, list, or other type)

    Returns:
        Sanitized copy of the data with sensitive fields redacted
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key is a sensitive field name (case-insensitive)
            if isinstance(key, str) and key.lower() in SENSITIVE_FIELD_NAMES:
                # Redact the value but preserve None
                sanitized[key] = "[REDACTED]" if value is not None else None
            else:
                # Recursively sanitize nested structures
                sanitized[key] = sanitize_dict(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_dict(item) for item in data)
    elif isinstance(data, str):
        # Sanitize string values that might contain sensitive data
        return sanitize_error_message(data)
    else:
        # Primitive types, return as-is
        return data


def sanitize_exception_details(exc: Exception) -> Dict[str, Any]:
    """
    Sanitize exception details for safe logging and client responses.

    This function extracts information from an exception and sanitizes it to prevent
    leaking sensitive data. It handles both custom exceptions with details attributes
    and standard Python exceptions.

    Args:
        exc: Exception to sanitize

    Returns:
        Dictionary with sanitized exception information
    """
    result = {
        "type": type(exc).__name__,
        "message": sanitize_error_message(str(exc)),
    }

    # If exception has a details attribute, sanitize it
    if hasattr(exc, "details") and exc.details:
        result["details"] = sanitize_dict(exc.details)

    # If exception has a status_code attribute, include it
    if hasattr(exc, "status_code") and exc.status_code:
        result["status_code"] = exc.status_code

    return result


def create_safe_error_response(error_message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a safe error response for API clients.

    This function creates a standardized error response with sanitized messages
    and details that are safe to send to clients.

    Args:
        error_message: The error message to include
        details: Optional additional error details

    Returns:
        Dictionary suitable for JSON API response
    """
    response = {"detail": sanitize_error_message(error_message)}

    if details:
        response["details"] = sanitize_dict(details)

    return response
