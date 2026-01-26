"""
Tests for custom exception hierarchy.

This module tests the custom exception classes defined in backend/app/exceptions.py,
verifying inheritance, attributes, and error messages.
"""

from backend.app.exceptions import (
    ViboMatException,
    AuthenticationError,
    TokenRefreshError,
    ExternalServiceError,
    SpotifyAPIError,
    ValidationError,
    InvalidPlaylistDataError,
    InfrastructureError,
    LockAcquisitionError,
    AIServiceError,
)


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""

    def test_vibomat_exception_is_base_exception(self):
        """Verify ViboMatException inherits from Exception."""
        exception = ViboMatException("test message")
        assert isinstance(exception, Exception)
        assert str(exception) == "test message"

    def test_authentication_error_inherits_from_base(self):
        """Verify AuthenticationError inherits from ViboMatException."""
        exception = AuthenticationError("auth failed")
        assert isinstance(exception, ViboMatException)
        assert isinstance(exception, Exception)
        assert str(exception) == "auth failed"

    def test_token_refresh_error_inherits_from_authentication(self):
        """Verify TokenRefreshError inherits from AuthenticationError."""
        exception = TokenRefreshError("token refresh failed")
        assert isinstance(exception, AuthenticationError)
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "token refresh failed"

    def test_external_service_error_inherits_from_base(self):
        """Verify ExternalServiceError inherits from ViboMatException."""
        exception = ExternalServiceError("service unavailable")
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "service unavailable"

    def test_spotify_api_error_inherits_from_external_service(self):
        """Verify SpotifyAPIError inherits from ExternalServiceError."""
        exception = SpotifyAPIError("spotify error")
        assert isinstance(exception, ExternalServiceError)
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "spotify error"

    def test_validation_error_inherits_from_base(self):
        """Verify ValidationError inherits from ViboMatException."""
        exception = ValidationError("invalid data")
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "invalid data"

    def test_invalid_playlist_data_error_inherits_from_validation(self):
        """Verify InvalidPlaylistDataError inherits from ValidationError."""
        exception = InvalidPlaylistDataError("invalid playlist")
        assert isinstance(exception, ValidationError)
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "invalid playlist"

    def test_infrastructure_error_inherits_from_base(self):
        """Verify InfrastructureError inherits from ViboMatException."""
        exception = InfrastructureError("infrastructure issue")
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "infrastructure issue"

    def test_lock_acquisition_error_inherits_from_infrastructure(self):
        """Verify LockAcquisitionError inherits from InfrastructureError."""
        exception = LockAcquisitionError("lock failed")
        assert isinstance(exception, InfrastructureError)
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "lock failed"

    def test_ai_service_error_inherits_from_external_service(self):
        """Verify AIServiceError inherits from ExternalServiceError."""
        exception = AIServiceError("AI service failed")
        assert isinstance(exception, ExternalServiceError)
        assert isinstance(exception, ViboMatException)
        assert str(exception) == "AI service failed"


class TestExceptionAttributes:
    """Test exception attributes and metadata."""

    def test_exception_with_status_code(self):
        """Verify exceptions can store HTTP status codes."""
        exception = AuthenticationError("unauthorized", status_code=401)
        assert exception.status_code == 401
        assert str(exception) == "unauthorized"

    def test_exception_with_details(self):
        """Verify exceptions can store additional details."""
        details = {"error_code": "INVALID_TOKEN", "retry_after": 60}
        exception = TokenRefreshError("token expired", details=details)
        assert exception.details == details
        assert exception.details is not None
        assert exception.details["error_code"] == "INVALID_TOKEN"

    def test_spotify_api_error_with_response_data(self):
        """Verify SpotifyAPIError can store API response data."""
        response_data = {"error": "invalid_grant", "error_description": "Token expired"}
        exception = SpotifyAPIError("Spotify API error", status_code=400, details=response_data)
        assert exception.status_code == 400
        assert exception.details is not None
        assert exception.details["error"] == "invalid_grant"

    def test_invalid_playlist_data_with_validation_errors(self):
        """Verify InvalidPlaylistDataError can store validation errors."""
        validation_errors = [
            {"field": "artist", "error": "Field required"},
            {"field": "duration_ms", "error": "Must be positive"},
        ]
        exception = InvalidPlaylistDataError("Validation failed", details={"errors": validation_errors})
        assert exception.details is not None
        assert len(exception.details["errors"]) == 2
        assert exception.details["errors"][0]["field"] == "artist"

    def test_exception_without_optional_attributes(self):
        """Verify exceptions work without optional attributes."""
        exception = ViboMatException("simple error")
        assert not hasattr(exception, "status_code") or exception.status_code is None
        assert not hasattr(exception, "details") or exception.details is None


class TestExceptionMessages:
    """Test exception message formatting."""

    def test_empty_message(self):
        """Verify exceptions handle empty messages."""
        exception = ViboMatException("")
        assert str(exception) == ""

    def test_multiline_message(self):
        """Verify exceptions handle multiline messages."""
        message = "Error occurred\nAdditional details\nMore info"
        exception = ViboMatException(message)
        assert str(exception) == message

    def test_exception_repr(self):
        """Verify exception repr includes class name and message."""
        exception = TokenRefreshError("token expired")
        repr_str = repr(exception)
        assert "TokenRefreshError" in repr_str
        assert "token expired" in repr_str
