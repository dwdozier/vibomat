"""
Tests for error message sanitization.

This module tests the error sanitizer that prevents sensitive information from
leaking in error messages sent to clients.
"""

from backend.app.core.error_sanitizer import (
    sanitize_error_message,
    sanitize_dict,
    SENSITIVE_PATTERNS,
)


class TestSanitizeErrorMessage:
    """Test error message sanitization."""

    def test_sanitize_access_token_in_message(self):
        """Verify access tokens are redacted from error messages."""
        message = "Failed with token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = sanitize_error_message(message)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_api_key_in_message(self):
        """Verify API keys are redacted from error messages."""
        message = "API error with api_key: sk-1234567890abcdef"
        sanitized = sanitize_error_message(message)
        assert "sk-1234567890abcdef" not in sanitized
        assert "[REDACTED_KEY]" in sanitized

    def test_sanitize_password_in_message(self):
        """Verify passwords are redacted from error messages."""
        message = "Authentication failed: password=SuperSecret123"
        sanitized = sanitize_error_message(message)
        assert "SuperSecret123" not in sanitized
        assert "[REDACTED_PASSWORD]" in sanitized

    def test_sanitize_email_in_message(self):
        """Verify email addresses are redacted from error messages."""
        message = "User not found: user@example.com"
        sanitized = sanitize_error_message(message)
        assert "user@example.com" not in sanitized
        assert "[REDACTED_EMAIL]" in sanitized

    def test_sanitize_database_connection_string(self):
        """Verify database connection strings are redacted."""
        message = "Connection failed: postgresql://user:pass@localhost:5432/db"
        sanitized = sanitize_error_message(message)
        assert "user:pass" not in sanitized
        assert "[REDACTED_CONNECTION_STRING]" in sanitized

    def test_sanitize_spotify_client_secret(self):
        """Verify Spotify client secrets are redacted."""
        message = "OAuth failed with secret: 56d4838dfdd847869dea8e87bc5f48e8"
        sanitized = sanitize_error_message(message)
        assert "56d4838dfdd847869dea8e87bc5f48e8" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_multiple_sensitive_values(self):
        """Verify multiple sensitive values are all redacted."""
        message = "Error: token=abc123, password=secret, email=test@example.com, " "api_key=sk-xyz789"
        sanitized = sanitize_error_message(message)
        assert "abc123" not in sanitized
        assert "secret" not in sanitized
        assert "test@example.com" not in sanitized
        assert "sk-xyz789" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_preserves_non_sensitive_content(self):
        """Verify non-sensitive content is preserved."""
        message = "User 'john_doe' failed to authenticate with service 'spotify'"
        sanitized = sanitize_error_message(message)
        assert "john_doe" in sanitized
        assert "authenticate" in sanitized
        assert "spotify" in sanitized

    def test_sanitize_empty_string(self):
        """Verify empty strings are handled correctly."""
        assert sanitize_error_message("") == ""

    def test_sanitize_none(self):
        """Verify None is handled correctly."""
        assert sanitize_error_message(None) == ""

    def test_sanitize_authorization_header(self):
        """Verify Authorization headers are redacted."""
        message = "Request failed with Authorization: Bearer token123456"
        sanitized = sanitize_error_message(message)
        assert "token123456" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_json_web_token(self):
        """Verify JWTs are redacted."""
        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        message = f"Token validation failed: {jwt}"
        sanitized = sanitize_error_message(message)
        assert jwt not in sanitized
        assert "[REDACTED_TOKEN]" in sanitized

    def test_sanitize_redis_url(self):
        """Verify Redis URLs with passwords are redacted."""
        message = "Redis error: redis://:password123@localhost:6379/0"
        sanitized = sanitize_error_message(message)
        assert "password123" not in sanitized
        assert "[REDACTED" in sanitized


class TestSanitizeDict:
    """Test dictionary sanitization."""

    def test_sanitize_dict_with_token(self):
        """Verify tokens in dictionaries are redacted."""
        data = {"access_token": "secret_token_123", "user": "testuser"}
        sanitized = sanitize_dict(data)
        assert sanitized["access_token"] == "[REDACTED]"
        assert sanitized["user"] == "testuser"

    def test_sanitize_dict_with_nested_data(self):
        """Verify nested dictionaries are sanitized."""
        data = {
            "user": {"name": "test", "password": "secret123"},
            "metadata": {"refresh_token": "token456"},
        }
        sanitized = sanitize_dict(data)
        assert sanitized["user"]["name"] == "test"
        assert sanitized["user"]["password"] == "[REDACTED]"
        assert sanitized["metadata"]["refresh_token"] == "[REDACTED]"

    def test_sanitize_dict_with_list(self):
        """Verify lists within dictionaries are sanitized."""
        data = {
            "tokens": [
                {"access_token": "token1", "type": "bearer"},
                {"access_token": "token2", "type": "bearer"},
            ]
        }
        sanitized = sanitize_dict(data)
        assert sanitized["tokens"][0]["access_token"] == "[REDACTED]"
        assert sanitized["tokens"][1]["access_token"] == "[REDACTED]"
        assert sanitized["tokens"][0]["type"] == "bearer"

    def test_sanitize_dict_preserves_structure(self):
        """Verify dictionary structure is preserved during sanitization."""
        data = {"level1": {"level2": {"level3": {"password": "secret", "public": "visible"}}}}
        sanitized = sanitize_dict(data)
        assert sanitized["level1"]["level2"]["level3"]["password"] == "[REDACTED]"
        assert sanitized["level1"]["level2"]["level3"]["public"] == "visible"

    def test_sanitize_dict_with_none_values(self):
        """Verify None values are preserved."""
        data = {"access_token": None, "user": "testuser"}
        sanitized = sanitize_dict(data)
        assert sanitized["access_token"] is None
        assert sanitized["user"] == "testuser"

    def test_sanitize_dict_case_insensitive(self):
        """Verify field name matching is case-insensitive."""
        data = {
            "Access_Token": "token1",
            "PASSWORD": "pass1",
            "Client_Secret": "secret1",
        }
        sanitized = sanitize_dict(data)
        assert sanitized["Access_Token"] == "[REDACTED]"
        assert sanitized["PASSWORD"] == "[REDACTED]"
        assert sanitized["Client_Secret"] == "[REDACTED]"

    def test_sanitize_non_dict(self):
        """Verify non-dict values are returned as-is."""
        assert sanitize_dict("string") == "string"
        assert sanitize_dict(123) == 123
        assert sanitize_dict(None) is None
        assert sanitize_dict([1, 2, 3]) == [1, 2, 3]


class TestSensitivePatterns:
    """Test sensitive pattern definitions."""

    def test_all_patterns_are_regex(self):
        """Verify all sensitive patterns are valid regex."""
        import re

        for pattern_info in SENSITIVE_PATTERNS:
            pattern = pattern_info["pattern"]
            # Should compile without error
            re.compile(pattern, re.IGNORECASE)

    def test_patterns_have_replacement(self):
        """Verify all patterns have replacement text."""
        for pattern_info in SENSITIVE_PATTERNS:
            assert "replacement" in pattern_info
            assert isinstance(pattern_info["replacement"], str)
            assert "[REDACTED" in pattern_info["replacement"]

    def test_jwt_pattern_matches_valid_jwt(self):
        """Verify JWT pattern matches valid JWT tokens."""
        import re

        jwt_pattern = next(p["pattern"] for p in SENSITIVE_PATTERNS if "TOKEN" in p["replacement"])
        valid_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        assert re.search(jwt_pattern, valid_jwt, re.IGNORECASE)

    def test_email_pattern_matches_valid_email(self):
        """Verify email pattern matches valid email addresses."""
        import re

        email_pattern = next(p["pattern"] for p in SENSITIVE_PATTERNS if "EMAIL" in p["replacement"])
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "admin+test@example.com",
        ]
        for email in valid_emails:
            assert re.search(email_pattern, email, re.IGNORECASE)

    def test_connection_string_pattern_matches_postgres(self):
        """Verify connection string pattern matches PostgreSQL URLs."""
        import re

        conn_pattern = next(p["pattern"] for p in SENSITIVE_PATTERNS if "CONNECTION_STRING" in p["replacement"])
        postgres_url = "postgresql://user:pass@localhost:5432/database"
        assert re.search(conn_pattern, postgres_url, re.IGNORECASE)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_sanitize_very_long_message(self):
        """Verify very long messages are handled correctly."""
        long_message = "Error: " + "x" * 10000 + " access_token=secret123456"
        sanitized = sanitize_error_message(long_message)
        assert "secret123456" not in sanitized
        assert len(sanitized) >= 100  # Should still have content

    def test_sanitize_unicode_message(self):
        """Verify unicode messages are handled correctly."""
        message = "Error: 用户认证失败 password=secret123"
        sanitized = sanitize_error_message(message)
        assert "secret123" not in sanitized
        assert "用户认证失败" in sanitized

    def test_sanitize_special_characters(self):
        """Verify special characters don't break sanitization."""
        message = "Error: token=abc$%^&*()123 failed"
        sanitized = sanitize_error_message(message)
        # Should still work, though pattern may not match all special chars
        assert isinstance(sanitized, str)

    def test_sanitize_recursive_dict(self):
        """Verify deeply nested structures are handled."""
        data = {"level1": {"level2": {"level3": {"level4": {"password": "secret"}}}}}
        sanitized = sanitize_dict(data)
        assert sanitized["level1"]["level2"]["level3"]["level4"]["password"] == "[REDACTED]"
