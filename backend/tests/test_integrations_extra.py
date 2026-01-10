import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.auth.fastapi_users import current_active_user
from unittest.mock import MagicMock, AsyncMock, patch
from backend.app.db.session import get_async_session
from backend.app.core.config import settings
import uuid


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_spotify_login_no_client_id(mock_user, mock_db):
    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with patch.object(settings, "SPOTIFY_CLIENT_ID", None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/integrations/spotify/login")

    assert response.status_code == 400
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_spotify_callback_no_creds(mock_db):
    app.dependency_overrides[get_async_session] = lambda: mock_db

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with patch.object(settings, "SPOTIFY_CLIENT_ID", None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/v1/integrations/spotify/callback?code=abc&state={uuid.uuid4()}")

    assert response.status_code == 400
    app.dependency_overrides.clear()
