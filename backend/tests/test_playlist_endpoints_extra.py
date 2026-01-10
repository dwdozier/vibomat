import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.auth.fastapi_users import current_active_user
from unittest.mock import MagicMock, AsyncMock
from backend.app.db.session import get_async_session
from backend.app.models.playlist import Playlist
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
async def test_get_playlist_endpoint(mock_user, mock_db):
    playlist = Playlist(
        id=uuid.uuid4(),
        user_id=mock_user.id,
        name="Test PL",
        public=True,
        content_json={"tracks": []},
        status="draft",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = playlist
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/playlists/{playlist.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test PL"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_playlist_not_found(mock_user, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/playlists/{uuid.uuid4()}")

    assert response.status_code == 404
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_playlist_endpoint(mock_user, mock_db):
    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    # Mock refresh to simulate DB generating an ID
    async def mock_refresh(instance):
        instance.id = uuid.uuid4()

    mock_db.refresh.side_effect = mock_refresh

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/playlists/", json={"name": "New PL", "description": "Desc", "tracks": []})

        assert response.status_code == 200
        assert response.json()["name"] == "New PL"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_playlist_endpoint(mock_user, mock_db):
    playlist = Playlist(
        id=uuid.uuid4(),
        user_id=mock_user.id,
        name="Old Name",
        status="draft",
        content_json={"tracks": []},
        public=False,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = playlist
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(f"/api/v1/playlists/{playlist.id}", json={"name": "New Name", "tracks": []})

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        assert playlist.name == "New Name"
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_playlist_endpoint(mock_user, mock_db):
    playlist = Playlist(id=uuid.uuid4(), user_id=mock_user.id, name="Test PL")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = playlist
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete(f"/api/v1/playlists/{playlist.id}")

    assert response.status_code == 204
    mock_db.commit.assert_called_once()
    app.dependency_overrides.clear()
