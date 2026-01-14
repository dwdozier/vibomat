from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from httpx import AsyncClient
from backend.core.metadata import MetadataVerifier
from backend.core.providers.spotify import SpotifyProvider

from backend.app.services.metadata_service import MetadataService
from backend.app.services.integrations_service import IntegrationsService


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
    with patch("backend.app.services.metadata_service.MetadataVerifier", spec=MetadataVerifier) as mock_cls:
        mock_instance = AsyncMock(spec=MetadataVerifier)
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def metadata_service(mock_httpx_client, mock_spotify_provider):
    """Fixture to instantiate MetadataService with a mock client."""
    return MetadataService(http_client=mock_httpx_client, spotify_provider=mock_spotify_provider)


async def test_metadata_service_enrich_artist(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful artist enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_artist.return_value = {"name": "Enriched", "id": "123"}

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_artist_info("Artist")
    assert result is not None
    assert result["name"] == "Enriched"
    mock_verifier.search_artist.assert_called_once_with("Artist")


async def test_metadata_service_enrich_album(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful album enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_album.return_value = {"title": "Album", "id": "456"}

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_album_info("Artist", "Album")
    assert result is not None
    assert result["name"] == "Album"
    mock_verifier.search_album.assert_called_once_with("Artist", "Album")


def test_integrations_service_init():
    """Test that IntegrationsService initializes correctly."""
    service = IntegrationsService(db=MagicMock())
    assert service.db is not None
