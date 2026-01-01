import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.testclient import TestClient
from backend.app.admin.auth import AdminAuth
from backend.app.admin.views import DashboardView
from backend.app.models.user import User
from backend.app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_dashboard_view():
    """Test the admin dashboard view."""
    view = DashboardView()
    mock_request = MagicMock(spec=Request)

    # Mock templates.TemplateResponse on the instance using patch
    with patch.object(view, "templates") as mock_templates:
        mock_templates.TemplateResponse = AsyncMock()

        func = getattr(view.index, "__wrapped__", view.index)
        await func(view, mock_request)

        mock_templates.TemplateResponse.assert_called_once()
        args, kwargs = mock_templates.TemplateResponse.call_args
        assert args[1] == "admin_dashboard.html"
        assert "title" in kwargs["context"]


def test_custom_admin_logout_route():
    """Test the custom /admin/logout route clears cookies."""
    response = client.get("/admin/logout", follow_redirects=False)
    assert response.status_code == 307 or response.status_code == 302
    assert response.headers["location"] == "/login"
    # Check if cookie is deleted (Max-Age=0)
    assert 'fastapiusersauth="";' in response.headers.get("set-cookie", "")
    assert "Max-Age=0" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_admin_auth_logout():
    """Test admin logout clears session."""
    mock_request = MagicMock(spec=Request)
    mock_request.session = MagicMock()

    auth_backend = AdminAuth(secret_key="secret")
    result = await auth_backend.logout(mock_request)

    assert result is True
    mock_request.session.clear.assert_called_once()


@pytest.mark.asyncio
async def test_admin_auth_success():
    """Test successful admin authentication."""
    # Mock request with session
    mock_request = MagicMock(spec=Request)
    mock_request.url = "http://testserver/admin/"
    mock_request.cookies = {"fastapiusersauth": "valid_token"}
    mock_request.session = {}

    # Mock user
    mock_user = MagicMock(spec=User)
    mock_user.is_superuser = True
    mock_user.email = "admin@example.com"

    # Mock dependencies
    with patch("backend.app.admin.auth.async_session_maker") as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch("backend.app.admin.auth.get_jwt_strategy") as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.read_token.return_value = mock_user
            mock_get_strategy.return_value = mock_strategy

            auth_backend = AdminAuth(secret_key="secret")

            # Test authenticate
            result = await auth_backend.authenticate(mock_request)

            assert result is True
            assert mock_request.session["token"] == "valid_superuser"


@pytest.mark.asyncio
async def test_admin_auth_fail_not_superuser():
    """Test admin authentication failure for non-superuser redirects to root."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"fastapiusersauth": "valid_token"}

    mock_user = MagicMock(spec=User)
    mock_user.is_superuser = False

    with patch("backend.app.admin.auth.async_session_maker") as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch("backend.app.admin.auth.get_jwt_strategy") as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.read_token.return_value = mock_user
            mock_get_strategy.return_value = mock_strategy

            auth_backend = AdminAuth(secret_key="secret")

            result = await auth_backend.authenticate(mock_request)

            assert isinstance(result, RedirectResponse)
            assert result.headers["location"] == "/"


@pytest.mark.asyncio
async def test_admin_auth_fail_no_token():
    """Test admin authentication failure when no token is present."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {}

    auth_backend = AdminAuth(secret_key="secret")
    result = await auth_backend.authenticate(mock_request)

    assert isinstance(result, RedirectResponse)


@pytest.mark.asyncio
async def test_admin_auth_fail_invalid_token():
    """Test admin authentication failure with invalid token."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"fastapiusersauth": "invalid"}

    with patch("backend.app.admin.auth.async_session_maker") as mock_session_maker:
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session

        with patch("backend.app.admin.auth.get_jwt_strategy") as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.read_token.return_value = None
            mock_get_strategy.return_value = mock_strategy

            auth_backend = AdminAuth(secret_key="secret")

            result = await auth_backend.authenticate(mock_request)

            assert isinstance(result, RedirectResponse)


@pytest.mark.asyncio
async def test_admin_auth_login_method():
    """Test login method of AdminAuth."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"fastapiusersauth": "valid"}

    mock_user = MagicMock(spec=User)
    mock_user.is_superuser = True

    with patch.object(AdminAuth, "_get_current_user", return_value=mock_user):
        auth_backend = AdminAuth(secret_key="secret")
        assert await auth_backend.login(mock_request) is True

    with patch.object(AdminAuth, "_get_current_user", return_value=None):
        auth_backend = AdminAuth(secret_key="secret")
        assert await auth_backend.login(mock_request) is False
