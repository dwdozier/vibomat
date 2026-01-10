from unittest.mock import MagicMock, patch, AsyncMock
from backend.app.core.tasks import create_playlist_task

# --- Shared Mocks for Spotify ---


class MockSpotifyClient:
    """Mocks the spotipy.Spotify client for testing."""

    def __init__(self, auth=None, **kwargs):
        self.auth = auth
        self.current_user = MagicMock(return_value={"id": "mock_user_id"})
        self.user_playlist_create = MagicMock(return_value={"id": "pl_id"})
        # Mock methods used in the provider to prevent network calls/validation failures
        self.playlist_replace_items = MagicMock()
        self.playlist_add_items = MagicMock()


# Patch the constructor of spotipy.Spotify itself
patch_spotipy_client = patch("backend.core.providers.spotify.spotipy.Spotify", new=MockSpotifyClient)

# --- Test Functions ---


async def test_create_playlist_task():
    """Test the create_playlist_task background worker."""

    with patch_spotipy_client:
        with patch("backend.app.core.tasks.SpotifyProvider") as mock_provider_cls:
            mock_provider = MagicMock()

            # The mocked SpotifyProvider should now use the MockSpotifyClient internally,
            # but we need to mock the async methods it calls on itself.
            mock_provider.create_playlist = AsyncMock(return_value="pl_id")
            mock_provider.add_tracks_to_playlist = AsyncMock()
            mock_provider_cls.return_value = mock_provider

            pl_id = await create_playlist_task("My Task Playlist", ["uri:1"], "token")

            assert pl_id == "pl_id"
            mock_provider.create_playlist.assert_called_once_with("My Task Playlist")
            mock_provider.add_tracks_to_playlist.assert_called_once_with("pl_id", ["uri:1"])


async def test_purge_deleted_playlists_task():
    """Test the purge_deleted_playlists_task."""
    from backend.app.core.tasks import purge_deleted_playlists_task
    from unittest.mock import AsyncMock

    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    mock_result = MagicMock()
    mock_result.rowcount = 5
    mock_session.execute.return_value = mock_result

    # Mock async context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.app.core.tasks.async_session_maker") as mock_maker:
        mock_maker.return_value = mock_session

        result = await purge_deleted_playlists_task()

        assert result == "Purged 5 playlists"
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


async def test_sync_playlist_task_success():
    """Test the successful execution of sync_playlist_task."""
    from backend.app.core.tasks import sync_playlist_task
    from backend.app.models.playlist import Playlist
    from backend.app.models.user import User
    from backend.app.models.service_connection import ServiceConnection
    from unittest.mock import AsyncMock
    import uuid

    # Mock DB Objects
    mock_user = MagicMock(spec=User, id=uuid.uuid4())
    mock_conn = MagicMock(spec=ServiceConnection, provider_name="spotify")
    mock_playlist = MagicMock(
        spec=Playlist,
        id=uuid.uuid4(),
        provider="spotify",
        provider_id="sp_id_123",
        user_id=mock_user.id,
        content_json={"tracks": [{"uri": "spotify:track:123", "provider": "spotify"}]},
    )

    # Mock DB Session.execute result
    mock_result = MagicMock()
    mock_result.first.return_value = (mock_playlist, mock_user, mock_conn)

    # Mock DB Session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    # Mock session context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch_spotipy_client:
        with (
            patch("backend.app.core.tasks.async_session_maker", return_value=mock_session),
            patch(
                "backend.app.core.tasks.IntegrationsService.get_valid_spotify_token",
                new=AsyncMock(return_value="valid_token"),
            ),
            patch("backend.app.core.tasks.SpotifyProvider") as MockProviderCls,
        ):
            mock_provider = MockProviderCls.return_value
            mock_provider.replace_playlist_tracks = AsyncMock()

            result = await sync_playlist_task(mock_playlist.id)

            assert "Sync successful" in result
            mock_provider.replace_playlist_tracks.assert_called_once_with("sp_id_123", ["spotify:track:123"])
            # Check if last_synced_at was updated (rough check for call, logic is in task)
            assert mock_playlist.last_synced_at is not None
            mock_session.commit.assert_called_once()


async def test_periodic_sync_dispatch_task():
    """Test that periodic_sync_dispatch_task correctly finds and dispatches tasks."""
    from backend.app.core.tasks import (
        periodic_sync_dispatch_task,
    )
    from unittest.mock import AsyncMock
    import uuid

    # Mock DB Session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    # Mock session context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    # Mock task dispatch
    with (
        patch("backend.app.core.tasks.async_session_maker", return_value=mock_session),
        patch("backend.app.core.tasks.sync_playlist_task") as mock_task,
    ):
        mock_task.kiq = AsyncMock()
        # Mock DB result with two playlist IDs
        pl1_id = uuid.uuid4()
        pl2_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pl1_id, pl2_id]
        mock_session.execute.return_value = mock_result

        result = await periodic_sync_dispatch_task()

        assert "Dispatched 2 sync tasks" in result
        # Check that the task was dispatched for both IDs
        mock_task.kiq.assert_any_call(pl1_id)
        mock_task.kiq.assert_any_call(pl2_id)
        assert mock_task.kiq.call_count == 2
