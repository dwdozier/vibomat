from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient

from backend.app.services.metadata_service import MetadataService
from backend.core.metadata import MetadataVerifier
from backend.core.providers.spotify import SpotifyProvider

# --- Fixtures ---


@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.AsyncClient to be passed to MetadataService."""
    mock_client = AsyncMock(spec=AsyncClient)
    yield mock_client


@pytest.fixture
def mock_spotify_provider():
    """Mocks the SpotifyProvider."""
    return AsyncMock(spec=SpotifyProvider)


@pytest.fixture
def mock_metadata_verifier_cls():
    """Mocks the MetadataVerifier class to track instantiations and methods."""
    # Ensure the class itself returns a mock instance suitable for awaiting its methods.
    with patch("backend.app.services.metadata_service.MetadataVerifier", spec=MetadataVerifier) as mock_cls:
        mock_instance = AsyncMock(spec=MetadataVerifier)
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def metadata_service(mock_httpx_client, mock_spotify_provider):
    """Fixture to instantiate MetadataService with a mock client."""
    return MetadataService(http_client=mock_httpx_client, spotify_provider=mock_spotify_provider)


# --- Metadata Service Enrichment Tests ---


async def test_metadata_service_enrich_artist_success(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful artist enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_data = {"id": "123", "name": "Test Artist", "type": "Group", "country": "US"}
    mock_verifier.search_artist.return_value = mock_data

    metadata_service = MetadataService(http_client=AsyncMock(), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_artist_info("Test Artist")

    assert result is not None
    assert result["name"] == "Test Artist"
    assert result["source_url"] == "https://musicbrainz.org/artist/123"
    mock_verifier.search_artist.assert_called_once_with("Test Artist")


async def test_metadata_service_enrich_artist_none(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test MetadataService when artist info is missing."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_artist.return_value = None

    metadata_service = MetadataService(http_client=AsyncMock(), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_artist_info("Unknown")
    assert result is None
    mock_verifier.search_artist.assert_called_once_with("Unknown")


async def test_metadata_service_enrich_album_success(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful album enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_data = {
        "id": "456",
        "title": "Test Album",
        "first-release-date": "2024-01-01",
        "primary-type": "Album",
    }
    mock_verifier.search_album.return_value = mock_data

    metadata_service = MetadataService(http_client=AsyncMock(), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_album_info("Test Artist", "Test Album")

    assert result is not None
    assert result["name"] == "Test Album"
    assert result["source_url"] == "https://musicbrainz.org/release-group/456"
    mock_verifier.search_album.assert_called_once_with("Test Artist", "Test Album")


async def test_metadata_service_enrich_album_none(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test MetadataService when album info is missing."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_album.return_value = None

    metadata_service = MetadataService(http_client=AsyncMock(), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_album_info("Artist", "Unknown")
    assert result is None
    mock_verifier.search_album.assert_called_once_with("Artist", "Unknown")
