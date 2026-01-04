import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.db.session import get_async_session
from backend.app.models.playlist import Playlist
import uuid

client = TestClient(app)

mock_user = MagicMock()
mock_user.id = uuid.uuid4()
mock_user.email = "test@example.com"


@pytest.fixture
def mock_db_session():
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    yield mock_db

    app.dependency_overrides.clear()


def test_create_playlist(mock_db_session):
    # Mock refresh to simulate DB assigning an ID
    def mock_refresh(obj):
        obj.id = uuid.uuid4()

    mock_db_session.refresh.side_effect = mock_refresh

    payload = {
        "name": "My Draft",
        "description": "Draft Desc",
        "public": False,
        "tracks": [{"artist": "A", "track": "T", "version": "studio"}],
    }

    response = client.post("/api/v1/playlists/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Draft"
    assert data["status"] == "draft"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_get_my_playlists(mock_db_session):
    # Mock DB result
    mock_playlist = MagicMock(spec=Playlist)
    mock_playlist.id = uuid.uuid4()
    mock_playlist.name = "My List"
    mock_playlist.description = "Desc"
    mock_playlist.public = False
    mock_playlist.user_id = mock_user.id
    mock_playlist.status = "draft"
    mock_playlist.provider = None
    mock_playlist.provider_id = None
    mock_playlist.total_duration_ms = None
    mock_playlist.content_json = {"tracks": []}

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_playlist]
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/playlists/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "My List"


def test_get_playlist_details(mock_db_session):
    pid = uuid.uuid4()
    mock_playlist = MagicMock(spec=Playlist)
    mock_playlist.id = pid
    mock_playlist.name = "Detail List"
    mock_playlist.description = "Desc"
    mock_playlist.public = False
    mock_playlist.user_id = mock_user.id
    mock_playlist.status = "draft"
    mock_playlist.provider = None
    mock_playlist.provider_id = None
    mock_playlist.total_duration_ms = None
    mock_playlist.content_json = {"tracks": []}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_playlist
    mock_db_session.execute.return_value = mock_result

    response = client.get(f"/api/v1/playlists/{pid}")

    assert response.status_code == 200
    assert response.json()["name"] == "Detail List"


def test_get_playlist_not_found(mock_db_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    response = client.get(f"/api/v1/playlists/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_playlist(mock_db_session):
    pid = uuid.uuid4()
    mock_playlist = MagicMock(spec=Playlist)
    mock_playlist.id = pid
    mock_playlist.user_id = mock_user.id
    mock_playlist.name = "Old Name"
    mock_playlist.status = "draft"
    mock_playlist.provider = None
    mock_playlist.provider_id = None
    mock_playlist.total_duration_ms = None

    mock_result = MagicMock()

    mock_result.scalar_one_or_none.return_value = mock_playlist
    mock_db_session.execute.return_value = mock_result

    payload = {"name": "New Name", "tracks": []}

    response = client.patch(f"/api/v1/playlists/{pid}", json=payload)

    assert response.status_code == 200
    assert mock_playlist.name == "New Name"
    mock_db_session.commit.assert_called_once()
