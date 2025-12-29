import pytest
from unittest.mock import MagicMock, patch
from backend.core.providers.spotify import SpotifyProvider


@pytest.fixture
def mock_spotipy():
    with patch("backend.core.providers.spotify.spotipy.Spotify") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        instance.current_user.return_value = {"id": "user_id"}
        yield instance


@pytest.mark.asyncio
async def test_spotify_provider_search_track(mock_spotipy):
    """Test SpotifyProvider search_track."""
    mock_spotipy.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:123",
                }
            ]
        }
    }

    provider = SpotifyProvider(auth_token="token")
    uri = await provider.search_track("Artist", "Song")
    assert uri == "spotify:track:123"


@pytest.mark.asyncio
async def test_spotify_provider_create_playlist(mock_spotipy):
    """Test SpotifyProvider create_playlist."""
    mock_spotipy.user_playlist_create.return_value = {"id": "pl_id"}

    provider = SpotifyProvider(auth_token="token")
    pl_id = await provider.create_playlist("My List")
    assert pl_id == "pl_id"
    mock_spotipy.user_playlist_create.assert_called_once()


@pytest.mark.asyncio
async def test_spotify_provider_add_tracks(mock_spotipy):
    """Test SpotifyProvider add_tracks_to_playlist."""
    provider = SpotifyProvider(auth_token="token")
    await provider.add_tracks_to_playlist("pl_id", ["uri:1"])
    mock_spotipy.playlist_add_items.assert_called_once_with("pl_id", ["uri:1"])
