"""
API Sanity Tests - Integration tests for API health and core functionality.

These tests should catch common issues before deployment:
- Missing dependencies (e.g., slowapi)
- Database connectivity
- Redis connectivity
- Rate limiting
- Basic endpoint functionality
"""

import pytest
import httpx


@pytest.mark.ci
def test_api_health_endpoint():
    """Test that the API health endpoint is responding."""
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code in [200, 429]  # OK or rate limited
    if response.status_code == 200:
        assert response.json() == {"status": "ok"}


@pytest.mark.ci
def test_api_rate_limiting_headers():
    """Test that rate limiting is configured and returning headers."""
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code in [200, 429]

    # Check for rate limit headers (slowapi provides these)
    headers = response.headers
    assert (
        "x-ratelimit-limit" in headers or "ratelimit-limit" in headers
    ), "Rate limit headers not found - is slowapi installed?"

    # If we get a successful response, verify the limit value
    if response.status_code == 200 and "x-ratelimit-limit" in headers:
        assert headers["x-ratelimit-limit"] == "100"  # Health endpoint: 100/minute


@pytest.mark.ci
def test_api_root_endpoint():
    """Test that the API root endpoint is responding."""
    response = httpx.get("http://localhost:8000/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Vib-O-Mat API" in data["message"]


@pytest.mark.ci
def test_api_database_connectivity():
    """Test that the API can connect to the database via auth endpoints."""
    # Try to access an authenticated endpoint (should get 401, not 500)
    response = httpx.get("http://localhost:8000/api/v1/users/me")
    assert response.status_code == 401  # Unauthorized, not 500 Internal Server Error
    assert response.json()["detail"] == "Unauthorized"


@pytest.mark.ci
def test_api_imports_and_dependencies():
    """
    Test that critical dependencies are imported correctly.

    This test attempts to trigger imports of key modules by accessing
    various endpoints. If dependencies like slowapi are missing, the
    API will fail to start or return 500 errors.
    """
    # Test rate-limited endpoint (requires slowapi)
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code in [200, 429], (
        f"Health endpoint failed with {response.status_code}. "
        "This might indicate missing dependencies (slowapi, etc.)"
    )

    # Test auth endpoints (requires fastapi-users, sqlalchemy)
    response = httpx.get("http://localhost:8000/api/v1/users/me")
    assert response.status_code == 401  # Should get unauthorized, not 500

    # Test root endpoint (basic FastAPI)
    response = httpx.get("http://localhost:8000/")
    assert response.status_code == 200
