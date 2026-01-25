import pytest
from backend.core.providers.spotify import SpotifyProvider


@pytest.mark.asyncio
async def test_spotify_provider_search_track(mock_spotify):
    """Test SpotifyProvider search_track."""
    mock_spotify.search.return_value = {
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
    result = await provider.search_track("Artist", "Song")
    assert result is not None
    assert result["uri"] == "spotify:track:123"


@pytest.mark.asyncio
async def test_spotify_provider_create_playlist(mock_spotify):
    """Test SpotifyProvider create_playlist."""
    mock_spotify.user_playlist_create.return_value = {"id": "pl_id"}

    provider = SpotifyProvider(auth_token="token")
    pl_id = await provider.create_playlist("My List")
    assert pl_id == "pl_id"
    mock_spotify.user_playlist_create.assert_called_once()


@pytest.mark.asyncio
async def test_spotify_provider_search_track_with_album(mock_spotify):
    """Test search_track with album."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:album",
                }
            ]
        }
    }
    provider = SpotifyProvider(auth_token="token")
    result = await provider.search_track("Artist", "Song", album="Album")
    assert result is not None
    assert result["uri"] == "spotify:track:album"


@pytest.mark.asyncio
async def test_spotify_provider_search_track_no_results(mock_spotify):
    """Test search_track with no results."""
    mock_spotify.search.return_value = {"tracks": {"items": []}}
    provider = SpotifyProvider(auth_token="token")
    uri = await provider.search_track("Artist", "Song")
    assert uri is None


@pytest.mark.asyncio
async def test_spotify_provider_search_track_no_version_pref(mock_spotify):
    """Test search_track with no version preference."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:studio",
                }
            ]
        }
    }
    provider = SpotifyProvider(auth_token="token")
    # No version passed, should prefer studio
    result = await provider.search_track("Artist", "Song")
    assert result is not None
    assert result["uri"] == "spotify:track:studio"


@pytest.mark.asyncio
async def test_spotify_provider_search_track_low_score(mock_spotify):
    """Test search_track with low score."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Different",
                    "artists": [{"name": "Other"}],
                    "album": {"name": "None"},
                    "uri": "spotify:track:low",
                }
            ]
        }
    }
    provider = SpotifyProvider(auth_token="token")
    uri = await provider.search_track("Artist", "Song")
    assert uri is None


@pytest.mark.asyncio
async def test_spotify_provider_add_tracks(mock_spotify):
    """Test SpotifyProvider add_tracks_to_playlist."""
    provider = SpotifyProvider(auth_token="token")
    await provider.add_tracks_to_playlist("pl_id", ["uri:1"])
    mock_spotify.playlist_add_items.assert_called_once_with("pl_id", ["uri:1"])
