import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from unittest.mock import MagicMock, AsyncMock
from backend.app.db.session import get_async_session

from backend.app.core.auth.fastapi_users import current_active_superuser


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user.id = "admin-id"
    user.is_superuser = True
    user.is_active = True
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_admin_stats_endpoint(mock_admin_user, mock_db):
    app.dependency_overrides[current_active_superuser] = lambda: mock_admin_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    # Mocking the execute result chain: db.execute().scalar()
    mock_result = MagicMock()
    mock_result.scalar.side_effect = [10, 5, 2, 1]  # users, playlists, connections, oauth
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["users"] == 10
    assert data["playlists"] == 5
    app.dependency_overrides.clear()
