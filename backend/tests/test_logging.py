"""
Tests for structured logging module.

This module tests the structured logging functionality including JSON formatting,
request_id correlation, and sensitive field sanitization.
"""

import json
import logging
from io import StringIO

from backend.app.core.logging import (
    get_logger,
    sanitize_log_data,
    REQUEST_ID_VAR,
)


class TestStructuredLogger:
    """Test the structured logger functionality."""

    def test_logger_creates_json_output(self):
        """Verify logger produces JSON-formatted output."""
        from backend.app.core.logging import CustomJsonFormatter

        # Create a string buffer to capture log output
        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.logger")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log a message
        logger.info("Test message", extra={"user_id": 123})

        # Get the log output
        log_output = log_buffer.getvalue()
        assert log_output.strip()  # Should have content

        # Parse as JSON
        log_record = json.loads(log_output)
        assert log_record["message"] == "Test message"
        assert log_record["level"] == "INFO"
        assert "timestamp" in log_record

    def test_logger_includes_request_id(self):
        """Verify logger includes request_id when available."""
        from backend.app.core.logging import CustomJsonFormatter

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.request_id")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Set request ID in context var
        token = REQUEST_ID_VAR.set("req-12345")

        try:
            logger.info("Request scoped message")
            log_output = log_buffer.getvalue()
            log_record = json.loads(log_output)
            assert log_record["request_id"] == "req-12345"
        finally:
            REQUEST_ID_VAR.reset(token)

    def test_logger_without_request_id(self):
        """Verify logger works without request_id."""
        from backend.app.core.logging import CustomJsonFormatter

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.no_request_id")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Ensure no request ID is set
        try:
            REQUEST_ID_VAR.get()
            REQUEST_ID_VAR.set(None)
        except LookupError:
            pass

        logger.info("Message without request ID")
        log_output = log_buffer.getvalue()
        log_record = json.loads(log_output)
        assert log_record["message"] == "Message without request ID"
        # request_id should either not be present or be null
        assert "request_id" not in log_record or log_record["request_id"] is None

    def test_logger_preserves_extra_fields(self):
        """Verify logger includes extra fields in output."""
        from backend.app.core.logging import CustomJsonFormatter

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.extra_fields")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Message with extras", extra={"user_id": 456, "action": "login", "ip": "127.0.0.1"})

        log_output = log_buffer.getvalue()
        log_record = json.loads(log_output)
        assert log_record["user_id"] == 456
        assert log_record["action"] == "login"
        assert log_record["ip"] == "127.0.0.1"


class TestSanitization:
    """Test sensitive field sanitization."""

    def test_sanitize_access_token(self):
        """Verify access tokens are redacted."""
        data = {"access_token": "secret_token_123", "user": "testuser"}
        sanitized = sanitize_log_data(data)
        assert sanitized["access_token"] == "[REDACTED]"
        assert sanitized["user"] == "testuser"

    def test_sanitize_refresh_token(self):
        """Verify refresh tokens are redacted."""
        data = {"refresh_token": "refresh_secret_456"}
        sanitized = sanitize_log_data(data)
        assert sanitized["refresh_token"] == "[REDACTED]"

    def test_sanitize_password(self):
        """Verify passwords are redacted."""
        data = {"password": "super_secret_pass"}
        sanitized = sanitize_log_data(data)
        assert sanitized["password"] == "[REDACTED]"

    def test_sanitize_api_key(self):
        """Verify API keys are redacted."""
        data = {"api_key": "key_123456", "client_secret": "secret_abc"}
        sanitized = sanitize_log_data(data)
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["client_secret"] == "[REDACTED]"

    def test_sanitize_nested_dict(self):
        """Verify sanitization works on nested dictionaries."""
        data = {"user": {"name": "test", "password": "secret"}, "public": "visible"}
        sanitized = sanitize_log_data(data)
        assert sanitized["user"]["name"] == "test"
        assert sanitized["user"]["password"] == "[REDACTED]"
        assert sanitized["public"] == "visible"

    def test_sanitize_list_of_dicts(self):
        """Verify sanitization works on lists containing dictionaries."""
        data = {
            "users": [
                {"name": "user1", "password": "pass1"},
                {"name": "user2", "access_token": "token2"},
            ]
        }
        sanitized = sanitize_log_data(data)
        assert sanitized["users"][0]["password"] == "[REDACTED]"
        assert sanitized["users"][1]["access_token"] == "[REDACTED]"
        assert sanitized["users"][0]["name"] == "user1"

    def test_sanitize_preserves_non_sensitive_data(self):
        """Verify non-sensitive fields are preserved."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "count": 42,
            "active": True,
            "tags": ["music", "playlist"],
        }
        sanitized = sanitize_log_data(data)
        assert sanitized == data  # Should be unchanged

    def test_sanitize_handles_non_dict(self):
        """Verify sanitization handles non-dict inputs gracefully."""
        assert sanitize_log_data("string") == "string"
        assert sanitize_log_data(123) == 123
        assert sanitize_log_data(None) is None
        assert sanitize_log_data([1, 2, 3]) == [1, 2, 3]

    def test_sanitize_case_insensitive(self):
        """Verify sanitization is case-insensitive for field names."""
        data = {"Access_Token": "token1", "PASSWORD": "pass1", "Api_Key": "key1"}
        sanitized = sanitize_log_data(data)
        assert sanitized["Access_Token"] == "[REDACTED]"
        assert sanitized["PASSWORD"] == "[REDACTED]"
        assert sanitized["Api_Key"] == "[REDACTED]"


class TestStructuredLoggerClass:
    """Test the StructuredLogger class directly."""

    def test_log_method_includes_sanitized_context(self):
        """Verify log method sanitizes context data."""
        from backend.app.core.logging import CustomJsonFormatter

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.sanitized_logging")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log with sensitive data
        logger.info("User login", extra={"user": "testuser", "password": "secret123"})

        log_output = log_buffer.getvalue()
        log_record = json.loads(log_output)

        assert log_record["user"] == "testuser"
        assert log_record["password"] == "[REDACTED]"

    def test_different_log_levels(self):
        """Verify different log levels work correctly."""
        from backend.app.core.logging import CustomJsonFormatter

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger = get_logger("test.log_levels")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Test different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        log_output = log_buffer.getvalue()
        log_lines = [line for line in log_output.strip().split("\n") if line]

        assert len(log_lines) == 4

        levels = [json.loads(line)["level"] for line in log_lines]
        assert levels == ["DEBUG", "INFO", "WARNING", "ERROR"]
