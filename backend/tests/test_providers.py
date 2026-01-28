import pytest
from backend.core.providers.spotify import SpotifyProvider
from backend.app.schemas.playlist import PlayabilityReason


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


# Playability Tests


@pytest.mark.asyncio
async def test_check_track_playability_playable(mock_spotify):
    """Test check_track_playability with a playable track."""
    mock_spotify.track.return_value = {
        "id": "123",
        "name": "Test Track",
        "is_playable": True,
        "available_markets": ["US", "CA", "GB"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.check_track_playability("spotify:track:123")

    assert result["playable"] is True
    assert result["reason"] == PlayabilityReason.PLAYABLE
    assert result["available_markets"] is None  # Not included for playable tracks
    assert result["is_local"] is False
    assert result["restrictions"] is None
    assert "checked_at" in result
    mock_spotify.track.assert_called_once_with("123", market="US")


@pytest.mark.asyncio
async def test_check_track_playability_region_restricted(mock_spotify):
    """Test check_track_playability with region-restricted track."""
    mock_spotify.track.return_value = {
        "id": "456",
        "name": "Restricted Track",
        "is_playable": False,
        "available_markets": ["JP", "KR"],
        "is_local": False,
        "restrictions": {"reason": "market"},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.check_track_playability("spotify:track:456")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.REGION_RESTRICTED
    assert result["available_markets"] == ["JP", "KR"]
    assert result["restrictions"] == {"reason": "market"}
    assert "checked_at" in result
    mock_spotify.track.assert_called_once_with("456", market="US")


@pytest.mark.asyncio
async def test_check_track_playability_explicit_content(mock_spotify):
    """Test check_track_playability with explicit content restriction."""
    mock_spotify.track.return_value = {
        "id": "789",
        "name": "Explicit Track",
        "is_playable": False,
        "available_markets": ["US"],
        "is_local": False,
        "restrictions": {"reason": "explicit"},
    }

    provider = SpotifyProvider(auth_token="token")
    result = await provider.check_track_playability("789", market="US")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.EXPLICIT_CONTENT_RESTRICTED
    assert result["restrictions"] == {"reason": "explicit"}
    assert "checked_at" in result


@pytest.mark.asyncio
async def test_check_track_playability_local_file(mock_spotify):
    """Test check_track_playability with local file."""
    mock_spotify.track.return_value = {
        "id": "local",
        "name": "Local File",
        "is_playable": False,
        "available_markets": [],
        "is_local": True,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token")
    result = await provider.check_track_playability("spotify:local:abc")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.LOCAL_FILE_ONLY
    assert result["is_local"] is True
    assert "checked_at" in result


@pytest.mark.asyncio
async def test_check_track_playability_unavailable(mock_spotify):
    """Test check_track_playability with unavailable track."""
    mock_spotify.track.return_value = {
        "id": "unavail",
        "name": "Unavailable Track",
        "is_playable": False,
        "available_markets": [],
        "is_local": False,
        "restrictions": {"reason": "unknown"},
    }

    provider = SpotifyProvider(auth_token="token")
    result = await provider.check_track_playability("spotify:track:unavail")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.UNAVAILABLE
    assert "checked_at" in result


@pytest.mark.asyncio
async def test_check_track_playability_api_error(mock_spotify):
    """Test check_track_playability handles API errors gracefully."""
    mock_spotify.track.side_effect = Exception("Spotify API error")

    provider = SpotifyProvider(auth_token="token")
    result = await provider.check_track_playability("spotify:track:error")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.UNKNOWN
    assert result["available_markets"] is None
    assert result["is_local"] is False
    assert result["restrictions"] is None
    assert "checked_at" in result


@pytest.mark.asyncio
async def test_check_track_playability_custom_market(mock_spotify):
    """Test check_track_playability with custom market override."""
    mock_spotify.track.return_value = {
        "id": "123",
        "name": "Test Track",
        "is_playable": True,
        "available_markets": ["GB"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.check_track_playability("spotify:track:123", market="GB")

    assert result["playable"] is True
    assert result["reason"] == PlayabilityReason.PLAYABLE
    # Should use the provided market "GB", not the instance market "US"
    mock_spotify.track.assert_called_once_with("123", market="GB")


@pytest.mark.asyncio
async def test_check_track_playability_no_market(mock_spotify):
    """Test check_track_playability with no market specified."""
    mock_spotify.track.return_value = {
        "id": "123",
        "name": "Test Track",
        "is_playable": True,
        "available_markets": ["US"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token")  # No market specified
    result = await provider.check_track_playability("spotify:track:123")

    assert result["playable"] is True
    assert result["reason"] == PlayabilityReason.PLAYABLE
    mock_spotify.track.assert_called_once_with("123", market=None)


@pytest.mark.asyncio
async def test_check_track_playability_market_not_in_available(mock_spotify):
    """Test check_track_playability when user market not in available markets."""
    mock_spotify.track.return_value = {
        "id": "123",
        "name": "Test Track",
        "is_playable": False,
        "available_markets": ["JP", "KR"],  # User market "US" not in list
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.check_track_playability("spotify:track:123")

    assert result["playable"] is False
    assert result["reason"] == PlayabilityReason.REGION_RESTRICTED
    assert result["available_markets"] == ["JP", "KR"]


@pytest.mark.asyncio
async def test_check_track_playability_default_is_playable(mock_spotify):
    """Test that is_playable defaults to True if not present in response."""
    mock_spotify.track.return_value = {
        "id": "123",
        "name": "Test Track",
        # is_playable not present
        "available_markets": ["US"],
        "is_local": False,
    }

    provider = SpotifyProvider(auth_token="token")
    result = await provider.check_track_playability("123")

    assert result["playable"] is True
    assert result["reason"] == PlayabilityReason.PLAYABLE


# Market Detection Tests


@pytest.mark.asyncio
async def test_get_user_market_success(mock_spotify):
    """Test get_user_market returns user's country code."""
    mock_spotify.current_user.return_value = {
        "id": "test_user_id",
        "country": "US",
        "display_name": "Test User",
        "email": "test@example.com",
    }

    provider = SpotifyProvider(auth_token="token")
    market = await provider.get_user_market()

    assert market == "US"
    mock_spotify.current_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_market_no_country(mock_spotify):
    """Test get_user_market when country is not available."""
    mock_spotify.current_user.return_value = {
        "id": "test_user_id",
        "display_name": "Test User",
        # country field missing
    }

    provider = SpotifyProvider(auth_token="token")
    market = await provider.get_user_market()

    assert market is None
    mock_spotify.current_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_market_api_error(mock_spotify):
    """Test get_user_market handles API errors."""
    mock_spotify.current_user.side_effect = Exception("Spotify API error")

    provider = SpotifyProvider(auth_token="token")

    with pytest.raises(Exception) as exc_info:
        await provider.get_user_market()

    assert "Spotify API error" in str(exc_info.value)
    mock_spotify.current_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_market_null_response(mock_spotify):
    """Test get_user_market when API returns None."""
    mock_spotify.current_user.return_value = None

    provider = SpotifyProvider(auth_token="token")

    with pytest.raises(Exception) as exc_info:
        await provider.get_user_market()

    assert "Failed to authenticate" in str(exc_info.value)
    mock_spotify.current_user.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_market_different_countries(mock_spotify):
    """Test get_user_market with various country codes."""
    test_countries = ["GB", "JP", "CA", "FR", "DE", "AU"]

    for country in test_countries:
        mock_spotify.current_user.return_value = {
            "id": "test_user_id",
            "country": country,
        }

        provider = SpotifyProvider(auth_token="token")
        market = await provider.get_user_market()

        assert market == country


# Enhanced Search with Playability Tests


@pytest.mark.asyncio
async def test_search_track_with_playability_check_playable(mock_spotify):
    """Test search_track with playability check for playable track."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                    "uri": "spotify:track:playable123",
                }
            ]
        }
    }

    # Mock track endpoint for playability check
    mock_spotify.track.return_value = {
        "id": "playable123",
        "name": "Test Track",
        "is_playable": True,
        "available_markets": ["US", "CA", "GB"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.search_track("Test Artist", "Test Track", check_playability=True)

    assert result is not None
    assert result["uri"] == "spotify:track:playable123"
    assert "playability" in result
    assert result["playability"]["playable"] is True
    assert result["playability"]["reason"] == PlayabilityReason.PLAYABLE
    mock_spotify.track.assert_called_once_with("playable123", market="US")


@pytest.mark.asyncio
async def test_search_track_with_playability_check_unplayable(mock_spotify):
    """Test search_track with playability check for unplayable track."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Restricted Track",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                    "uri": "spotify:track:restricted456",
                }
            ]
        }
    }

    # Mock track endpoint for playability check
    mock_spotify.track.return_value = {
        "id": "restricted456",
        "name": "Restricted Track",
        "is_playable": False,
        "available_markets": ["JP", "KR"],
        "is_local": False,
        "restrictions": {"reason": "market"},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.search_track("Test Artist", "Restricted Track", check_playability=True)

    assert result is not None
    assert result["uri"] == "spotify:track:restricted456"
    assert "playability" in result
    assert result["playability"]["playable"] is False
    assert result["playability"]["reason"] == PlayabilityReason.REGION_RESTRICTED
    assert result["playability"]["available_markets"] == ["JP", "KR"]


@pytest.mark.asyncio
async def test_search_track_with_album_and_playability(mock_spotify):
    """Test search_track with album and playability check."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Album Track",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Specific Album"},
                    "uri": "spotify:track:album789",
                }
            ]
        }
    }

    mock_spotify.track.return_value = {
        "id": "album789",
        "name": "Album Track",
        "is_playable": True,
        "available_markets": ["US"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token", market="US")
    result = await provider.search_track("Artist", "Album Track", album="Specific Album", check_playability=True)

    assert result is not None
    assert result["uri"] == "spotify:track:album789"
    assert result["album"] == "Specific Album"
    assert "playability" in result
    assert result["playability"]["playable"] is True


@pytest.mark.asyncio
async def test_search_track_without_playability_check(mock_spotify):
    """Test search_track without playability check (default behavior)."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Normal Track",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:normal123",
                }
            ]
        }
    }

    provider = SpotifyProvider(auth_token="token")
    result = await provider.search_track("Artist", "Normal Track")

    assert result is not None
    assert result["uri"] == "spotify:track:normal123"
    assert "playability" not in result
    # track() should not be called when check_playability=False
    mock_spotify.track.assert_not_called()


@pytest.mark.asyncio
async def test_search_track_playability_no_market(mock_spotify):
    """Test search_track with playability check but no market specified."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Track",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:nomarket",
                }
            ]
        }
    }

    mock_spotify.track.return_value = {
        "id": "nomarket",
        "name": "Track",
        "is_playable": True,
        "available_markets": ["US"],
        "is_local": False,
        "restrictions": {},
    }

    provider = SpotifyProvider(auth_token="token")  # No market
    result = await provider.search_track("Artist", "Track", check_playability=True)

    assert result is not None
    assert "playability" in result
    # Should call track() with market=None
    mock_spotify.track.assert_called_once_with("nomarket", market=None)
