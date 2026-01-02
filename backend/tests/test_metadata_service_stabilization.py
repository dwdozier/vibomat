import pytest
from unittest.mock import patch
from backend.core.metadata import MetadataVerifier
from backend.app.services.metadata_service import MetadataService


@pytest.fixture
def mock_mb_search():
    with patch("backend.core.metadata.MetadataVerifier.search_recording") as mock:
        yield mock


@pytest.fixture
def mock_discogs_search():
    with patch("backend.core.metadata.DiscogsVerifier.search_recording") as mock:
        yield mock


@pytest.fixture
def mock_discogs_token():
    with patch("backend.core.metadata.get_discogs_token", return_value="fake_token"):
        yield


def test_metadata_service_get_artist_info_success():
    service = MetadataService()
    mock_data = {"id": "123", "name": "Artist", "type": "Group", "country": "US"}
    with patch.object(service.verifier, "search_artist", return_value=mock_data):
        info = service.get_artist_info("Artist")
        assert info is not None
        assert info["name"] == "Artist"
        assert info["id"] == "123"
        assert info["source_name"] == "MusicBrainz"


def test_metadata_service_get_artist_info_not_found():
    service = MetadataService()
    with patch.object(service.verifier, "search_artist", return_value=None):
        info = service.get_artist_info("Unknown")
        assert info is None


def test_metadata_service_get_album_info_success():
    service = MetadataService()
    mock_data = {
        "id": "456",
        "title": "Album",
        "first-release-date": "2020-01-01",
        "primary-type": "Album",
    }
    with patch.object(service.verifier, "search_album", return_value=mock_data):
        info = service.get_album_info("Artist", "Album")
        assert info is not None
        assert info["name"] == "Album"
        assert info["id"] == "456"
        assert info["source_name"] == "MusicBrainz"


def test_metadata_service_get_album_info_not_found():
    service = MetadataService()
    with patch.object(service.verifier, "search_album", return_value=None):
        info = service.get_album_info("Artist", "Unknown")
        assert info is None


# Edge cases for MetadataVerifier


def test_verify_track_version_mb_exception(mock_mb_search, mock_discogs_search, mock_discogs_token):
    """Test that if MusicBrainz raises an exception, we still try Discogs."""
    verifier = MetadataVerifier()

    # MB raises exception
    mock_mb_search.side_effect = Exception("MB Down")

    # Discogs succeeds
    mock_discogs_search.return_value = [{"title": "Song (Live)", "format": ["CD"]}]

    result = verifier.verify_track_version("Artist", "Song", "live")
    assert result is True
    mock_mb_search.assert_called_once()
    mock_discogs_search.assert_called_once()


def test_verify_track_version_both_fail_no_token(mock_mb_search, mock_discogs_search):
    """Test that if MB fails and no Discogs token, return False."""
    verifier = MetadataVerifier()

    mock_mb_search.return_value = []

    # Simulate no token environment
    with patch("backend.core.metadata.get_discogs_token", return_value=None):
        result = verifier.verify_track_version("Artist", "Song", "live")
        assert result is False
