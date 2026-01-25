import pytest
import httpx
import uuid
from unittest.mock import MagicMock, AsyncMock
from backend.app.main import app
from backend.app.models.user import User
from backend.app.core.auth.fastapi_users import current_active_superuser


@pytest.mark.asyncio
async def test_admin_stats_endpoint(db_session):
    """Test the admin stats endpoint."""
    # Mock a superuser
    mock_admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )

    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_superuser] = lambda: mock_admin

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "playlists" in data
        assert "connections" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_list_users(db_session):
    """Test listing all users as admin."""
    mock_admin = User(
        id=uuid.uuid4(),
        email="admin2@example.com",
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )
    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_superuser] = lambda: mock_admin

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_list_playlists(db_session):
    """Test listing all playlists as admin."""
    mock_admin = User(
        id=uuid.uuid4(),
        email="admin3@example.com",
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )
    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_superuser] = lambda: mock_admin

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/playlists")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_list_connections(db_session):
    """Test listing all connections as admin."""
    mock_admin = User(
        id=uuid.uuid4(),
        email="admin4@example.com",
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )
    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_superuser] = lambda: mock_admin

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/connections")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_stats_unauthorized():
    """Test that non-admins cannot access stats."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/stats")
        assert response.status_code in [401, 403]


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
async def test_admin_stats_endpoint_mocked(mock_admin_user, mock_db):
    """Test the admin stats endpoint with mocked database values."""
    from backend.app.db.session import get_async_session
    from backend.app.core.auth.fastapi_users import current_active_superuser

    app.dependency_overrides[current_active_superuser] = lambda: mock_admin_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    # Mocking the execute result chain: db.execute().scalar_one_or_none() or .scalar()
    # The API uses .scalar_one_or_none(). Let's mock .scalar for compatibility with the original extra test.
    mock_result = MagicMock()
    mock_result.scalar.side_effect = [10, 5, 2, 1]
    mock_db.execute.return_value = mock_result

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["users"] == 10
    assert data["playlists"] == 5
    assert data["connections"] == 2
    assert data["oauth_accounts"] == 1
    app.dependency_overrides.clear()
