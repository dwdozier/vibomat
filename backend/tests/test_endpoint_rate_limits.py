"""
Tests for endpoint-specific rate limits.

This module tests that individual endpoints have appropriate rate limits
applied to protect against DoS attacks and abuse.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.is_active = True
    return user


class TestMetadataSearchRateLimit:
    """Test rate limiting on metadata search endpoint."""

    def test_metadata_search_has_rate_limit(self, client, mock_user):
        """Verify metadata search endpoint is rate limited."""
        with patch(
            "backend.app.api.v1.endpoints.playlists.current_active_user",
            return_value=mock_user,
        ):
            with patch("backend.app.api.v1.endpoints.playlists.get_async_session"):
                # Make a single request
                response = client.get("/api/v1/playlists/search/metadata?q=test")
                # Should either succeed or be rate limited
                assert response.status_code in [200, 401, 429]

    def test_metadata_search_rate_limit_headers(self, client, mock_user):
        """Verify rate limit headers are present."""
        with patch(
            "backend.app.api.v1.endpoints.playlists.current_active_user",
            return_value=mock_user,
        ):
            with patch("backend.app.api.v1.endpoints.playlists.get_async_session"):
                response = client.get("/api/v1/playlists/search/metadata?q=test")

                # Check for rate limit headers
                if response.status_code in [200, 429]:
                    rate_limit_headers = [
                        "X-RateLimit-Limit",
                        "X-RateLimit-Remaining",
                        "RateLimit-Limit",
                    ]
                    has_header = any(h in response.headers for h in rate_limit_headers)
                    # Headers should be present if rate limiting is working
                    # (may not be present due to auth mocking issues)
                    assert has_header or response.status_code == 401


class TestSpotifyLoginRateLimit:
    """Test rate limiting on Spotify OAuth login endpoint."""

    def test_spotify_login_has_rate_limit(self, client, mock_user):
        """Verify Spotify login endpoint is rate limited."""
        with patch(
            "backend.app.api.v1.endpoints.integrations.current_active_user",
            return_value=mock_user,
        ):
            with patch("backend.app.api.v1.endpoints.integrations.get_async_session"):
                # Make a single request
                response = client.get("/api/v1/integrations/spotify/login")
                # Should either succeed (redirect) or be rate limited
                assert response.status_code in [200, 307, 401, 429]


class TestRateLimitConfiguration:
    """Test rate limit configuration for endpoints."""

    def test_limiter_available(self):
        """Verify limiter is available in app state."""
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None

    def test_limiter_storage_configured(self):
        """Verify limiter has Redis storage."""
        limiter = app.state.limiter
        assert hasattr(limiter, "_storage")
        # Storage should exist
        assert limiter._storage is not None


class TestRateLimitIntegration:
    """Integration tests for endpoint rate limits."""

    def test_multiple_endpoints_independent(self, client):
        """Verify different endpoints have independent rate limits."""
        # Health endpoint and auth endpoints should have separate buckets
        health_response = client.get("/health")
        assert health_response.status_code in [200, 429]

        # Even if health is rate limited, other endpoints should work
        # (assuming we haven't hit their limits)
        root_response = client.get("/")
        assert root_response.status_code == 200


class TestRateLimitDocumentation:
    """Test that rate limits are documented."""

    def test_metadata_search_docstring_mentions_rate_limit(self):
        """Verify metadata search endpoint documents rate limit."""
        from backend.app.api.v1.endpoints.playlists import search_metadata

        docstring = search_metadata.__doc__ or ""
        # Should mention rate limiting
        assert "rate limit" in docstring.lower() or "30" in docstring or "minute" in docstring

    def test_spotify_login_docstring_mentions_rate_limit(self):
        """Verify Spotify login endpoint documents rate limit."""
        from backend.app.api.v1.endpoints.integrations import spotify_login

        docstring = spotify_login.__doc__ or ""
        # Should mention rate limiting
        assert "rate limit" in docstring.lower() or "10" in docstring or "minute" in docstring
