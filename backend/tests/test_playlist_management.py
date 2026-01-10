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


def test_import_playlist_success(mock_db_session):
    from unittest.mock import patch

    mock_conn = MagicMock()
    mock_conn.user_id = mock_user.id
    mock_conn.provider_name = "spotify"

    # Mock Int Service and Provider
    with (
        patch("backend.app.api.v1.endpoints.playlists.IntegrationsService") as MockIntService,
        patch("backend.core.providers.spotify.SpotifyProvider") as MockProviderCls,
    ):

        mock_int_service = MockIntService.return_value
        mock_int_service.get_valid_spotify_token = AsyncMock(return_value="fake_token")

        mock_provider = MockProviderCls.return_value
        mock_provider.get_playlist = AsyncMock(
            return_value={
                "name": "Imported List",
                "description": "Desc",
                "public": True,
                "tracks": {
                    "items": [
                        {
                            "track": {
                                "name": "Song 1",
                                "artists": [{"name": "Artist 1"}],
                                "album": {"name": "Album 1"},
                                "duration_ms": 30000,
                                "uri": "spotify:track:123",
                            }
                        }
                    ]
                },
            }
        )

        # Mock DB execute: first call returns connection
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_conn

        def mock_refresh(obj):
            obj.id = uuid.uuid4()
            obj.status = "imported"

        mock_db_session.refresh.side_effect = mock_refresh

        payload = {
            "provider": "spotify",
            "provider_playlist_id": "sp_id_123",
            "import_tracks": True,
        }

        response = client.post("/api/v1/playlists/import", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Imported List"
        assert data["provider"] == "spotify"
        assert len(data["content_json"]["tracks"]) == 1
        assert data["content_json"]["tracks"][0]["uri"] == "spotify:track:123"

        mock_int_service.get_valid_spotify_token.assert_called_once()
        mock_provider.get_playlist.assert_called_once_with("sp_id_123")

        class PlaylistStub:

            def __init__(self, **kwargs):

                for k, v in kwargs.items():

                    setattr(self, k, v)

                # Ensure default attributes are set for the endpoint logic

                self.deleted_at = None

                self.provider = self.provider if hasattr(self, "provider") else None

                self.provider_id = self.provider_id if hasattr(self, "provider_id") else None

        @pytest.mark.asyncio
        async def test_sync_endpoint_success(mock_db_session):

            from unittest.mock import patch

            pid = uuid.uuid4()

            mock_playlist = PlaylistStub(
                id=pid,
                user_id=mock_user.id,
                provider="spotify",
                provider_id="sp_id_123",
            )

            mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist

            with patch("backend.app.api.v1.endpoints.playlists.sync_playlist_task") as mock_sync_task:

                response = client.post(f"/api/v1/playlists/{pid}/sync")

                assert response.status_code == 200

                assert response.json()["message"] == "Playlist synchronization task enqueued"

                # Check if the task was dispatched

                mock_sync_task.kiq.assert_called_once_with(pid)

        @pytest.mark.asyncio
        async def test_sync_endpoint_not_linked(mock_db_session):

            pid = uuid.uuid4()

            mock_playlist = PlaylistStub(
                id=pid,
                user_id=mock_user.id,
                provider=None,  # Not linked
                provider_id=None,
            )

            mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist

            response = client.post(f"/api/v1/playlists/{pid}/sync")

            assert response.status_code == 400

            assert "not linked to a remote service" in response.json()["detail"]

        @pytest.mark.asyncio
        async def test_sync_endpoint_unauthorized(mock_db_session):

            pid = uuid.uuid4()

            mock_playlist = PlaylistStub(
                id=pid,
                user_id=uuid.uuid4(),  # Different user ID
                provider="spotify",
                provider_id="sp_id_123",
            )

            mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_playlist

            response = client.post(f"/api/v1/playlists/{pid}/sync")

            assert response.status_code == 403

            assert "Not authorized to sync this playlist" in response.json()["detail"]
