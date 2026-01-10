import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.auth.fastapi_users import current_active_user
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_async_session
from backend.app.api.v1.endpoints.users import get_metadata_service
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
import uuid


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "550e8400-e29b-41d4-a716-446655440000"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.mark.asyncio
async def test_enrich_artist_endpoint(mock_user):
    mock_service = AsyncMock()
    mock_service.get_artist_info.return_value = {"name": "Test Artist"}

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_metadata_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/profile/me/enrich/artist", json={"artist_name": "Artist"})

    assert response.status_code == 200
    assert response.json()["name"] == "Test Artist"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enrich_album_endpoint(mock_user):
    mock_service = AsyncMock()
    mock_service.get_album_info.return_value = {"name": "Test Album"}

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_metadata_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/profile/me/enrich/album", json={"artist_name": "Artist", "album_name": "Album"}
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Album"
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user_obj():
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        handle="testuser",
        is_public=True,
        is_active=True,
        first_name="Test",
        favorite_artists=[],
        unskippable_albums=[],
    )
    return user


@pytest.mark.asyncio
async def test_get_public_profile_by_handle(mock_db, mock_user_obj):
    mock_result = MagicMock()
    mock_result.unique.return_value.scalar_one_or_none.return_value = mock_user_obj
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/profile/by-handle/{mock_user_obj.handle}")

    assert response.status_code == 200
    assert response.json()["handle"] == mock_user_obj.handle
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_public_profile(mock_db, mock_user_obj):
    mock_result = MagicMock()
    mock_result.unique.return_value.scalar_one_or_none.return_value = mock_user_obj
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/profile/{mock_user_obj.id}")

    assert response.status_code == 200
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_public_playlists(mock_db, mock_user_obj):
    # Mock user check
    mock_user_result = MagicMock()
    mock_user_result.unique.return_value.scalar_one_or_none.return_value = mock_user_obj

    # Mock playlists check
    mock_playlist = Playlist(
        id=uuid.uuid4(),
        name="Public PL",
        public=True,
        deleted_at=None,
        user_id=mock_user_obj.id,
        content_json={"tracks": []},
        status="draft",
    )

    mock_pl_result = MagicMock()
    mock_pl_result.scalars.return_value.all.return_value = [mock_playlist]

    mock_db.execute.side_effect = [mock_user_result, mock_pl_result]

    app.dependency_overrides[get_async_session] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/profile/{mock_user_obj.id}/playlists")

    assert response.status_code == 200
    assert len(response.json()) == 1
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_favorite_playlist(mock_db, mock_user, mock_user_obj):
    # Mock playlist check
    mock_playlist = Playlist(
        id=uuid.uuid4(),
        name="Fav PL",
        public=True,
        deleted_at=None,
        user_id=mock_user_obj.id,
        content_json={"tracks": []},
        status="draft",
    )

    mock_pl_result = MagicMock()
    mock_pl_result.scalar_one_or_none.return_value = mock_playlist

    # Mock already favorited check
    mock_fav_result = MagicMock()
    mock_fav_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_pl_result, mock_fav_result, MagicMock()]

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/profile/playlists/{mock_playlist.id}/favorite")

    assert response.status_code == 200
    assert response.json()["message"] == "Playlist favorited"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_preferences_endpoint(mock_user):
    app.dependency_overrides[current_active_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.patch("/api/v1/profile/me/preferences", json={"discogs_pat": "new-pat"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    app.dependency_overrides.clear()
