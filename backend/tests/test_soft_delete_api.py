import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.db.session import get_async_session
from sqlalchemy.sql import Select
import uuid
from datetime import datetime, timezone

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


def test_get_my_playlists_filters_deleted(mock_db_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/playlists/me")

    assert response.status_code == 200

    # Verify the query has the deleted_at is None condition
    args, kwargs = mock_db_session.execute.call_args
    stmt = args[0]
    assert isinstance(stmt, Select)

    # Check if 'deleted_at IS NULL' is in the compiled query
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "playlist.deleted_at IS NULL" in compiled


def test_get_playlist_filters_deleted(mock_db_session):
    pid = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    response = client.get(f"/api/v1/playlists/{pid}")

    # Should be 404 because we returned None from mock
    assert response.status_code == 404

    # Verify the query has the deleted_at is None condition
    args, kwargs = mock_db_session.execute.call_args
    stmt = args[0]
    assert isinstance(stmt, Select)

    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "playlist.deleted_at IS NULL" in compiled


def test_delete_playlist_soft_deletes(mock_db_session):
    pid = uuid.uuid4()
    mock_playlist = MagicMock()
    mock_playlist.user_id = mock_user.id
    mock_playlist.deleted_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_playlist
    mock_db_session.execute.return_value = mock_result

    response = client.delete(f"/api/v1/playlists/{pid}")

    assert response.status_code == 204
    assert mock_playlist.deleted_at is not None
    mock_db_session.commit.assert_called_once()


def test_restore_playlist_recovers(mock_db_session):
    pid = uuid.uuid4()
    mock_playlist = MagicMock()
    mock_playlist.id = pid
    mock_playlist.user_id = mock_user.id
    mock_playlist.name = "Restored Playlist"
    mock_playlist.description = "Restored Desc"
    mock_playlist.public = False
    mock_playlist.status = "draft"
    mock_playlist.content_json = {"tracks": []}
    mock_playlist.provider = None
    mock_playlist.provider_id = None
    mock_playlist.deleted_at = datetime.now(timezone.utc)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_playlist
    mock_db_session.execute.return_value = mock_result

    response = client.post(f"/api/v1/playlists/{pid}/restore")

    assert response.status_code == 200
    assert mock_playlist.deleted_at is None
    mock_db_session.commit.assert_called_once()
