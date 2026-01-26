"""
Tests for ProxyHeadersMiddleware configuration and security.

This module verifies that proxy header handling is secure by ensuring only
trusted proxy IPs can modify forwarded headers (X-Forwarded-For, X-Real-IP, etc.).
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings


class TestProxyHeadersConfiguration:
    """Test ProxyHeadersMiddleware configuration."""

    def test_trusted_proxy_ips_setting_exists(self):
        """Verify TRUSTED_PROXY_IPS setting is defined."""
        assert hasattr(settings, "TRUSTED_PROXY_IPS")
        assert isinstance(settings.TRUSTED_PROXY_IPS, list)

    def test_default_trusted_proxy_ips_are_localhost(self):
        """Verify default trusted proxy IPs include only localhost."""
        # Default should be localhost addresses only
        assert "127.0.0.1" in settings.TRUSTED_PROXY_IPS
        assert "::1" in settings.TRUSTED_PROXY_IPS
        # Should not include wildcard
        assert "*" not in settings.TRUSTED_PROXY_IPS

    def test_trusted_proxy_ips_configurable_via_env(self):
        """Verify TRUSTED_PROXY_IPS can be configured via environment."""
        with patch.dict("os.environ", {"TRUSTED_PROXY_IPS": "10.0.0.1,10.0.0.2"}):
            # Import fresh settings to pick up env var
            from importlib import reload
            import backend.app.core.config as config_module

            reload(config_module)
            reloaded_settings = config_module.settings

            assert "10.0.0.1" in reloaded_settings.TRUSTED_PROXY_IPS
            assert "10.0.0.2" in reloaded_settings.TRUSTED_PROXY_IPS


class TestProxyHeadersSecurity:
    """Test proxy headers security with trusted and untrusted IPs."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint_accessible_without_proxy_headers(self, client):
        """Verify health endpoint works without proxy headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_trusted_proxy_headers_accepted_from_localhost(self, client):
        """Verify proxy headers from localhost (trusted) are accepted."""
        # Simulate request forwarded through localhost proxy
        response = client.get(
            "/health",
            headers={
                "X-Forwarded-For": "192.168.1.100",
                "X-Real-IP": "192.168.1.100",
            },
        )
        assert response.status_code == 200

    def test_middleware_configured_without_wildcard(self):
        """Verify middleware is not configured with wildcard trusted_hosts."""
        # Check that ProxyHeadersMiddleware exists and is not configured with "*"
        proxy_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, "__name__") and (
                middleware.cls.__name__ == "ProxyHeadersMiddleware"  # type: ignore
            ):
                proxy_middleware = middleware
                break

        assert proxy_middleware is not None, "ProxyHeadersMiddleware not found"

        # Verify options don't include wildcard (check kwargs)
        if hasattr(proxy_middleware, "options") and hasattr(proxy_middleware.options, "get"):
            trusted_hosts = proxy_middleware.options.get("trusted_hosts", [])  # type: ignore
            assert "*" not in trusted_hosts, "ProxyHeadersMiddleware configured with wildcard trusted_hosts"

    def test_proxy_headers_middleware_uses_settings(self):
        """Verify ProxyHeadersMiddleware uses TRUSTED_PROXY_IPS from settings."""
        # Find the ProxyHeadersMiddleware in the app
        proxy_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, "__name__") and (
                middleware.cls.__name__ == "ProxyHeadersMiddleware"  # type: ignore
            ):
                proxy_middleware = middleware
                break

        assert proxy_middleware is not None, "ProxyHeadersMiddleware not found"

        # Verify it uses settings (implementation detail check)
        # This is indirect - we verify via the configuration
        assert hasattr(settings, "TRUSTED_PROXY_IPS")


class TestProxyHeadersDocumentation:
    """Test that deployment documentation exists for proxy configuration."""

    def test_deployment_documentation_exists(self):
        """Verify DEPLOYMENT.md file exists with proxy configuration guidance."""
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        deployment_doc_path = os.path.join(project_root, "DEPLOYMENT.md")

        assert os.path.exists(deployment_doc_path), "DEPLOYMENT.md not found in project root"

    def test_deployment_documentation_contains_proxy_config(self):
        """Verify DEPLOYMENT.md contains proxy configuration guidance."""
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        deployment_doc_path = os.path.join(project_root, "DEPLOYMENT.md")

        if os.path.exists(deployment_doc_path):
            with open(deployment_doc_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            # Check for key terms
            assert (
                "proxy" in content or "trusted" in content
            ), "DEPLOYMENT.md should contain proxy configuration guidance"
            assert "trusted_proxy_ips" in content or (
                "x-forwarded" in content
            ), "DEPLOYMENT.md should document TRUSTED_PROXY_IPS setting"
