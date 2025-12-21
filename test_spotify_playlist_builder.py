import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure we can import the script from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from spotify_playlist_builder import SpotifyPlaylistBuilder, get_credentials_from_env


@pytest.fixture
def mock_spotify():
    """Mock the spotipy.Spotify client."""
    with patch("spotify_playlist_builder.spotipy.Spotify") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        # Mock successful authentication
        instance.current_user.return_value = {"id": "test_user_id"}
        yield instance


@pytest.fixture
def builder(mock_spotify):
    """Create a SpotifyPlaylistBuilder instance with mocked dependencies."""
    with patch("spotify_playlist_builder.SpotifyOAuth"):
        return SpotifyPlaylistBuilder("fake_client_id", "fake_client_secret")


def test_get_credentials_from_env_success():
    """Test retrieving credentials from environment variables."""
    env_vars = {"SPOTIFY_CLIENT_ID": "test_id", "SPOTIFY_CLIENT_SECRET": "test_secret"}
    with patch.dict(os.environ, env_vars):
        cid, secret = get_credentials_from_env()
        assert cid == "test_id"
        assert secret == "test_secret"


def test_get_credentials_from_env_missing():
    """Test error when environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception) as exc:
            get_credentials_from_env()
        assert "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found" in str(exc.value)


def test_search_track_exact_match(builder, mock_spotify):
    """Test searching for a track that returns an exact match."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Test Song",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                    "uri": "spotify:track:123",
                }
            ]
        }
    }

    uri = builder.search_track("Test Artist", "Test Song")
    assert uri == "spotify:track:123"


def test_search_track_fuzzy_match(builder, mock_spotify):
    """Test the fuzzy matching logic selects the best candidate."""
    # Mock search returning multiple results
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Irrelevant Song",
                    "artists": [{"name": "Other Artist"}],
                    "album": {"name": "Album A"},
                    "uri": "spotify:track:999",
                },
                {
                    "name": "Target Song",
                    "artists": [{"name": "Target Artist"}],
                    "album": {"name": "Target Album"},
                    "uri": "spotify:track:456",
                },
            ]
        }
    }

    # Should match the second item based on string similarity
    uri = builder.search_track("Target Artist", "Target Song")
    assert uri == "spotify:track:456"


def test_create_playlist(builder, mock_spotify):
    """Test playlist creation parameters."""
    mock_spotify.user_playlist_create.return_value = {"id": "new_pid"}

    pid = builder.create_playlist("My List", "Description", public=False)

    assert pid == "new_pid"
    mock_spotify.user_playlist_create.assert_called_with(
        user="test_user_id", name="My List", public=False, description="Description"
    )


def test_add_tracks_to_playlist_batching(builder, mock_spotify):
    """Test that tracks are added in batches of 100."""
    with patch.object(builder, "search_track", return_value="spotify:track:1"):
        # Create 105 dummy tracks
        tracks = [{"artist": "A", "track": "B"}] * 105
        builder.add_tracks_to_playlist("pid", tracks)

        # Should be called twice: once for 100 tracks, once for 5 tracks
        assert mock_spotify.playlist_add_items.call_count == 2
