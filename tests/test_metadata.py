import pytest
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
    """Test verification returns True for default/studio version without checking API."""
    with patch.object(verifier, "search_recording") as mock_search:
        assert verifier.verify_track_version("Artist", "Track", "studio") is True
        assert verifier.verify_track_version("Artist", "Track", None) is True
        mock_search.assert_not_called()


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
    """Test verification returns False when no matching version found."""
    mock_recordings = [{"title": "Song", "disambiguation": ""}]

    with patch.object(verifier, "search_recording", return_value=mock_recordings):
        assert verifier.verify_track_version("Artist", "Song", "live") is False
