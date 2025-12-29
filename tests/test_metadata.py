import pytest
import os
from unittest.mock import MagicMock, patch
from spotify_playlist_builder.metadata import MetadataVerifier
import requests


@pytest.fixture
def verifier():
    return MetadataVerifier()


def test_search_recording_success(verifier):
    """Test successful search for a recording."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"recordings": [{"title": "Test Song", "id": "123"}]}
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get:
        results = verifier.search_recording("Artist", "Track")

        assert results == [{"title": "Test Song", "id": "123"}]
        mock_get.assert_called_once()


def test_search_recording_api_error(verifier):
    """Test handling of MusicBrainz API errors."""
    from tenacity import RetryError

    with patch("requests.get", side_effect=requests.exceptions.RequestException("API Error")):
        with pytest.raises(RetryError):
            verifier.search_recording("Artist", "Track")


def test_search_recording_unexpected_error(verifier):
    """Test handling of unexpected errors (json parsing failure)."""
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("JSON Error")

    with patch("requests.get", return_value=mock_response):
        results = verifier.search_recording("Artist", "Track")
        assert results == []


def test_verify_track_version_default(verifier):
    """Test verification checks API for default/studio version."""
    mock_recordings = [{"title": "Song", "disambiguation": ""}]
    with patch.object(verifier, "search_recording", return_value=mock_recordings) as mock_search:
        assert verifier.verify_track_version("Artist", "Track", "studio") is True
        assert verifier.verify_track_version("Artist", "Track", None) is True
        # Should be called twice
        assert mock_search.call_count == 2


def test_verify_track_version_live_match(verifier):
    """Test verification for live version match."""
    mock_recordings = [
        {"title": "Song", "disambiguation": "Studio"},
        {"title": "Song (Live)", "disambiguation": "Live at Venue"},
    ]

    with patch.object(verifier, "search_recording", return_value=mock_recordings):
        assert verifier.verify_track_version("Artist", "Song", "live") is True


def test_verify_track_version_remix_match(verifier):
    """Test verification for remix version match."""
    mock_recordings = [{"title": "Song Remix", "disambiguation": ""}]

    with patch.object(verifier, "search_recording", return_value=mock_recordings):
        assert verifier.verify_track_version("Artist", "Song", "remix") is True


def test_verify_track_version_remaster_match(verifier):
    """Test verification for remaster version match."""
    mock_recordings = [{"title": "Song", "disambiguation": "2011 Remaster"}]

    with patch.object(verifier, "search_recording", return_value=mock_recordings):
        assert verifier.verify_track_version("Artist", "Song", "remaster") is True


def test_verify_track_version_no_match(verifier):
    """Test verification returns False when no matching version found in MB (fallback fail)."""
    mock_recordings = [{"title": "Song", "disambiguation": ""}]

    # We need to ensure Discogs also fails or is not called for this legacy test
    with (
        patch.object(verifier, "search_recording", return_value=mock_recordings),
        patch.object(verifier.discogs, "verify_track_version", return_value=False),
    ):
        assert verifier.verify_track_version("Artist", "Song", "live") is False


# --- Discogs Direct Tests for Coverage ---


def test_get_discogs_token_env():
    """Test retrieving Discogs token from env."""
    with patch.dict(os.environ, {"DISCOGS_PAT": "env_token"}):
        from spotify_playlist_builder.metadata import get_discogs_token

        assert get_discogs_token() == "env_token"


def test_get_discogs_token_keyring():
    """Test retrieving Discogs token from keyring."""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = "keyring_token"
    with (
        patch.dict(os.environ, {}, clear=True),
        patch.dict("sys.modules", {"keyring": mock_keyring}),
    ):
        from spotify_playlist_builder.metadata import get_discogs_token

        assert get_discogs_token() == "keyring_token"


def test_get_discogs_token_error():
    """Test get_discogs_token handles errors gracefully."""
    mock_keyring = MagicMock()
    mock_keyring.get_password.side_effect = Exception("Keyring Error")
    with (
        patch.dict(os.environ, {}, clear=True),
        patch.dict("sys.modules", {"keyring": mock_keyring}),
    ):
        from spotify_playlist_builder.metadata import get_discogs_token

        assert get_discogs_token() is None


def test_discogs_search_recording_success():
    """Test DiscogsVerifier.search_recording logic."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value="init_token"):
        verifier = DiscogsVerifier()

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": [{"title": "Artist - Track"}]}
    mock_resp.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_resp) as mock_get:
        results = verifier.search_recording("Artist", "Track")
        assert results == [{"title": "Artist - Track"}]
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "Authorization" in kwargs["headers"]


def test_discogs_search_recording_api_error():
    """Test DiscogsVerifier handles API errors gracefully."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value="t"):
        verifier = DiscogsVerifier()

    with patch("requests.get", side_effect=requests.exceptions.RequestException("API Error")):
        results = verifier.search_recording("Artist", "Track")
        assert results == []


def test_discogs_search_recording_unexpected_error():
    """Test DiscogsVerifier handles unexpected errors gracefully."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value="t"):
        verifier = DiscogsVerifier()

    mock_resp = MagicMock()
    mock_resp.json.side_effect = ValueError("JSON Error")
    with patch("requests.get", return_value=mock_resp):
        results = verifier.search_recording("Artist", "Track")
        assert results == []


def test_discogs_verify_track_version_match():
    """Test DiscogsVerifier.verify_track_version logic."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value="t"):
        verifier = DiscogsVerifier()

    # Test Live match
    with patch.object(verifier, "search_recording", return_value=[{"title": "Song (Live)"}]):
        assert verifier.verify_track_version("Artist", "Song", "live") is True

    # Test Remix match
    with patch.object(verifier, "search_recording", return_value=[{"title": "Song (Remix)"}]):
        assert verifier.verify_track_version("Artist", "Song", "remix") is True

    # Test Studio match (implicit)
    with patch.object(verifier, "search_recording", return_value=[{"title": "Song"}]):
        assert verifier.verify_track_version("Artist", "Song", "studio") is True

    # Test No match
    with patch.object(verifier, "search_recording", return_value=[{"title": "Other Song"}]):
        assert verifier.verify_track_version("Artist", "Song", "live") is False


# --- Discogs Fallback Tests ---


@pytest.fixture
def mock_mb_search():
    with patch("spotify_playlist_builder.metadata.MetadataVerifier.search_recording") as mock:
        yield mock


@pytest.fixture
def mock_discogs_search():
    with patch("spotify_playlist_builder.metadata.DiscogsVerifier.search_recording") as mock:
        yield mock


@pytest.fixture
def mock_discogs_token():
    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value="fake_token"):
        yield


def test_verify_track_mb_success(mock_mb_search, mock_discogs_search):
    """Test that if MusicBrainz succeeds, Discogs is not called."""
    verifier = MetadataVerifier()

    # MB returns a match
    mock_mb_search.return_value = [{"title": "Test Song", "disambiguation": "Live at Wembley"}]

    # We verify 'live' version
    result = verifier.verify_track_version("Artist", "Test Song", "live")

    assert result is True
    mock_mb_search.assert_called_once()
    mock_discogs_search.assert_not_called()


def test_verify_track_mb_fail_discogs_success(
    mock_mb_search, mock_discogs_search, mock_discogs_token
):
    """Test that if MusicBrainz fails/empty, Discogs is called and succeeds."""
    verifier = MetadataVerifier()

    # MB returns empty
    mock_mb_search.return_value = []

    # Discogs returns a match
    mock_discogs_search.return_value = [{"title": "Test Song (Live)", "format": ["CD"]}]

    result = verifier.verify_track_version("Artist", "Test Song", "live")

    assert result is True
    mock_mb_search.assert_called_once()
    mock_discogs_search.assert_called_once()


def test_verify_track_both_fail(mock_mb_search, mock_discogs_search, mock_discogs_token):
    """Test that if both fail, returns False."""
    verifier = MetadataVerifier()

    mock_mb_search.return_value = []
    mock_discogs_search.return_value = []

    result = verifier.verify_track_version("Artist", "Nonexistent Song", "studio")

    assert result is False
    mock_mb_search.assert_called_once()
    mock_discogs_search.assert_called_once()


def test_verify_track_discogs_no_token(mock_mb_search, mock_discogs_search):
    """Test that Discogs is skipped if no token is present."""
    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value=None):
        verifier = MetadataVerifier()

        mock_mb_search.return_value = []

        result = verifier.verify_track_version("Artist", "Song", "studio")

        assert result is False
        mock_discogs_search.assert_not_called()


def test_discogs_search_no_token():
    """Test search returns empty list if no token."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value=None):
        verifier = DiscogsVerifier()
        assert verifier.search_recording("Artist", "Track") == []


def test_discogs_verify_no_token():
    """Test verify returns False if no token."""
    from spotify_playlist_builder.metadata import DiscogsVerifier

    with patch("spotify_playlist_builder.metadata.get_discogs_token", return_value=None):
        verifier = DiscogsVerifier()
        assert verifier.verify_track_version("Artist", "Track", "studio") is False
