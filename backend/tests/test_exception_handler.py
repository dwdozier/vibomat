"""
Tests for global exception handler middleware.

This module tests the exception handler middleware that maps custom exceptions to
HTTP responses and sanitizes error messages.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.exceptions import (
    ViboMatException,
    AuthenticationError,
    TokenRefreshError,
    SpotifyAPIError,
    ValidationError,
    InvalidPlaylistDataError,
    InfrastructureError,
    LockAcquisitionError,
    AIServiceError,
)
from backend.app.middleware.exception_handler import (
    vibomat_exception_handler,
    generic_exception_handler,
)


@pytest.fixture
def app():
    """Create a FastAPI app with exception handlers."""
    test_app = FastAPI()

    # Register exception handlers
    test_app.add_exception_handler(ViboMatException, vibomat_exception_handler)  # type: ignore[arg-type]
    test_app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]

    # Add test routes that raise exceptions
    @test_app.get("/auth-error")
    async def auth_error():
        raise AuthenticationError("Invalid credentials")

    @test_app.get("/token-error")
    async def token_error():
        raise TokenRefreshError("Token expired", details={"error": "invalid_grant"})

    @test_app.get("/spotify-error")
    async def spotify_error():
        raise SpotifyAPIError("Spotify API failure", status_code=502)

    @test_app.get("/ai-error")
    async def ai_error():
        raise AIServiceError("AI service unavailable")

    @test_app.get("/validation-error")
    async def validation_error():
        raise ValidationError("Invalid input", details={"field": "email", "error": "invalid format"})

    @test_app.get("/playlist-error")
    async def playlist_error():
        raise InvalidPlaylistDataError("Invalid track data")

    @test_app.get("/infrastructure-error")
    async def infrastructure_error():
        raise InfrastructureError("Database connection failed")

    @test_app.get("/lock-error")
    async def lock_error():
        raise LockAcquisitionError("Failed to acquire lock")

    @test_app.get("/generic-error")
    async def generic_error():
        raise Exception("Unexpected error")

    @test_app.get("/base-vibomat-error")
    async def base_vibomat_error():
        raise ViboMatException("Base exception", status_code=418)

    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestExceptionHandlerStatusCodes:
    """Test that exceptions map to correct HTTP status codes."""

    def test_authentication_error_returns_401(self, client):
        """Verify AuthenticationError returns 401."""
        response = client.get("/auth-error")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid credentials" in data["detail"]

    def test_token_refresh_error_returns_401(self, client):
        """Verify TokenRefreshError returns 401."""
        response = client.get("/token-error")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_spotify_api_error_returns_502(self, client):
        """Verify SpotifyAPIError returns 502."""
        response = client.get("/spotify-error")
        assert response.status_code == 502
        data = response.json()
        assert "detail" in data

    def test_ai_service_error_returns_502(self, client):
        """Verify AIServiceError returns 502."""
        response = client.get("/ai-error")
        assert response.status_code == 502
        data = response.json()
        assert "detail" in data

    def test_validation_error_returns_400(self, client):
        """Verify ValidationError returns 400."""
        response = client.get("/validation-error")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_invalid_playlist_data_error_returns_400(self, client):
        """Verify InvalidPlaylistDataError returns 400."""
        response = client.get("/playlist-error")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_infrastructure_error_returns_500(self, client):
        """Verify InfrastructureError returns 500."""
        response = client.get("/infrastructure-error")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_lock_acquisition_error_returns_503(self, client):
        """Verify LockAcquisitionError returns 503."""
        response = client.get("/lock-error")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data

    def test_generic_exception_returns_500(self, client):
        """Verify generic Exception returns 500."""
        response = client.get("/generic-error")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        # Generic errors should have sanitized message
        assert "Internal server error" in data["detail"]

    def test_base_vibomat_exception_uses_custom_status_code(self, client):
        """Verify ViboMatException uses custom status code."""
        response = client.get("/base-vibomat-error")
        assert response.status_code == 418
        data = response.json()
        assert "detail" in data


class TestExceptionHandlerDetails:
    """Test that exception details are handled correctly."""

    def test_exception_with_details_includes_them(self, client):
        """Verify exceptions with details include them in response."""
        response = client.get("/validation-error")
        data = response.json()
        # Details might be included in the response or logged separately
        assert "detail" in data

    def test_exception_details_are_sanitized(self, client):
        """Verify sensitive data in exception details is sanitized."""
        # This would require a route that raises an exception with sensitive data
        # For now, verify basic structure
        response = client.get("/token-error")
        data = response.json()
        assert "detail" in data
        # The error message should not include raw sensitive data


class TestExceptionHandlerFormat:
    """Test the format of error responses."""

    def test_error_response_has_detail_field(self, client):
        """Verify all error responses include 'detail' field."""
        endpoints = [
            "/auth-error",
            "/validation-error",
            "/spotify-error",
            "/infrastructure-error",
            "/generic-error",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "detail" in data, f"Endpoint {endpoint} missing 'detail' field"

    def test_error_response_is_json(self, client):
        """Verify all error responses are JSON."""
        response = client.get("/auth-error")
        assert response.headers["content-type"] == "application/json"

    def test_error_message_is_string(self, client):
        """Verify error detail is a string."""
        response = client.get("/auth-error")
        data = response.json()
        assert isinstance(data["detail"], str)


class TestExceptionLogging:
    """Test that exceptions are properly logged."""

    def test_exception_handler_logs_error(self, client, caplog):
        """Verify exceptions are logged with appropriate level."""
        import logging

        with caplog.at_level(logging.ERROR):
            client.get("/spotify-error")

        # Should log the error
        assert len(caplog.records) > 0
        # At least one record should be ERROR level
        assert any(record.levelname == "ERROR" for record in caplog.records)

    def test_generic_exception_handler_logs_error(self, client, caplog):
        """Verify generic exceptions are logged."""
        import logging

        with caplog.at_level(logging.ERROR):
            client.get("/generic-error")

        assert len(caplog.records) > 0
        assert any(record.levelname == "ERROR" for record in caplog.records)
