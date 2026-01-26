"""
Custom exception hierarchy for Vibomat application.

This module defines a comprehensive exception hierarchy for handling various error
scenarios throughout the application. All custom exceptions inherit from ViboMatException
for centralized error handling.

Exception Hierarchy:
    ViboMatException (base)
    ├── AuthenticationError
    │   └── TokenRefreshError
    ├── ExternalServiceError
    │   ├── SpotifyAPIError
    │   └── AIServiceError
    ├── ValidationError
    │   └── InvalidPlaylistDataError
    └── InfrastructureError
        └── LockAcquisitionError
"""

from typing import Any, Dict, Optional


class ViboMatException(Exception):
    """
    Base exception class for all Vibomat custom exceptions.

    All custom exceptions in the application should inherit from this class to enable
    centralized exception handling and logging.

    Attributes:
        message: Human-readable error message
        status_code: Optional HTTP status code for API responses
        details: Optional dictionary containing additional error context
    """

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code (optional)
            details: Additional error context (optional)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def __repr__(self) -> str:
        """Return a detailed representation of the exception."""
        return f"{self.__class__.__name__}('{self.message}')"


class AuthenticationError(ViboMatException):
    """
    Raised when authentication or authorization fails.

    This includes issues with user credentials, access tokens, API keys, and other
    authentication mechanisms.
    """

    def __init__(self, message: str, status_code: Optional[int] = 401, details: Optional[Dict[str, Any]] = None):
        """Initialize authentication error with default 401 status code."""
        super().__init__(message, status_code, details)


class TokenRefreshError(AuthenticationError):
    """
    Raised when OAuth token refresh fails.

    This exception is raised when attempting to refresh an expired access token fails,
    typically due to an invalid refresh token, revoked authorization, or API errors.
    """

    def __init__(self, message: str, status_code: Optional[int] = 401, details: Optional[Dict[str, Any]] = None):
        """Initialize token refresh error."""
        super().__init__(message, status_code, details)


class ExternalServiceError(ViboMatException):
    """
    Raised when external service integration fails.

    This includes errors from Spotify API, MusicBrainz, Discogs, AI services, and other
    third-party APIs.
    """

    def __init__(self, message: str, status_code: Optional[int] = 502, details: Optional[Dict[str, Any]] = None):
        """Initialize external service error with default 502 status code."""
        super().__init__(message, status_code, details)


class SpotifyAPIError(ExternalServiceError):
    """
    Raised when Spotify API requests fail.

    This exception captures errors from the Spotify Web API, including rate limiting,
    invalid requests, authorization issues, and service unavailability.
    """

    def __init__(self, message: str, status_code: Optional[int] = 502, details: Optional[Dict[str, Any]] = None):
        """Initialize Spotify API error."""
        super().__init__(message, status_code, details)


class AIServiceError(ExternalServiceError):
    """
    Raised when AI service (Gemini, etc.) requests fail.

    This exception is raised when playlist generation or other AI-powered features
    encounter errors from the underlying AI service provider.
    """

    def __init__(self, message: str, status_code: Optional[int] = 502, details: Optional[Dict[str, Any]] = None):
        """Initialize AI service error."""
        super().__init__(message, status_code, details)


class ValidationError(ViboMatException):
    """
    Raised when input validation fails.

    This includes schema validation errors, invalid field values, missing required
    fields, and other data validation issues.
    """

    def __init__(self, message: str, status_code: Optional[int] = 400, details: Optional[Dict[str, Any]] = None):
        """Initialize validation error with default 400 status code."""
        super().__init__(message, status_code, details)


class InvalidPlaylistDataError(ValidationError):
    """
    Raised when playlist content validation fails.

    This exception is raised when playlist data (tracks, metadata, etc.) does not meet
    the required schema or contains malformed data.
    """

    def __init__(self, message: str, status_code: Optional[int] = 400, details: Optional[Dict[str, Any]] = None):
        """Initialize invalid playlist data error."""
        super().__init__(message, status_code, details)


class InfrastructureError(ViboMatException):
    """
    Raised when infrastructure operations fail.

    This includes database errors, Redis connection issues, distributed locking
    failures, and other infrastructure-related problems.
    """

    def __init__(self, message: str, status_code: Optional[int] = 500, details: Optional[Dict[str, Any]] = None):
        """Initialize infrastructure error with default 500 status code."""
        super().__init__(message, status_code, details)


class LockAcquisitionError(InfrastructureError):
    """
    Raised when distributed lock acquisition fails.

    This exception is raised when a process cannot acquire a required distributed lock,
    typically due to timeout, lock contention, or Redis connectivity issues.
    """

    def __init__(self, message: str, status_code: Optional[int] = 503, details: Optional[Dict[str, Any]] = None):
        """Initialize lock acquisition error with default 503 status code."""
        super().__init__(message, status_code, details)
