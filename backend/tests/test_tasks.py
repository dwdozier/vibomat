from unittest.mock import MagicMock, patch
from backend.app.core.tasks import create_playlist_task


async def test_create_playlist_task():
    """Test the create_playlist_task background worker."""
    from unittest.mock import AsyncMock

    with patch("backend.core.providers.spotify.SpotifyProvider") as mock_provider_cls:
        mock_provider = MagicMock()
        mock_provider.create_playlist = AsyncMock(return_value="pl_id")
        mock_provider.add_tracks_to_playlist = AsyncMock()
        mock_provider_cls.return_value = mock_provider

        pl_id = await create_playlist_task("My Task Playlist", ["uri:1"], "token")

        assert pl_id == "pl_id"
        mock_provider.create_playlist.assert_called_once_with("My Task Playlist")
        mock_provider.add_tracks_to_playlist.assert_called_once_with("pl_id", ["uri:1"])
