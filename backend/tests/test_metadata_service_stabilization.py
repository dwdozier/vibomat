from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient

from backend.core.metadata import MetadataVerifier, MusicBrainzAPIError
from backend.core.providers.discogs import DiscogsClient
from backend.app.services.metadata_service import MetadataService

# --- Fixtures ---


@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.AsyncClient to be passed to MetadataService."""
    mock_client = AsyncMock(spec=AsyncClient)
    yield mock_client


@pytest.fixture
def mock_metadata_verifier_cls():
    """Mocks the MetadataVerifier class to track instantiations and methods."""
    with patch("backend.app.services.metadata_service.MetadataVerifier", spec=MetadataVerifier) as mock_cls:
        # The class mock needs to return an AsyncMock instance when instantiated by the service
        mock_instance = AsyncMock(spec=MetadataVerifier)
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def metadata_service(mock_httpx_client):
    """Fixture to instantiate MetadataService with a mock client."""
    return MetadataService(http_client=mock_httpx_client)


# --- Service Tests (formerly sync, now async) ---


async def test_metadata_service_get_artist_info_success(mock_metadata_verifier_cls):
    """Test successful fetching of artist info."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_data = {"id": "123", "name": "Artist", "type": "Group", "country": "US"}
    mock_verifier.search_artist.return_value = mock_data

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient))
    info = await metadata_service.get_artist_info("Artist")
    assert info is not None
    assert info["name"] == "Artist"
    assert info["id"] == "123"
    assert info["source_name"] == "MusicBrainz"
    mock_verifier.search_artist.assert_called_once_with("Artist")


async def test_metadata_service_get_artist_info_not_found(mock_metadata_verifier_cls):
    """Test MetadataService when artist info is not found."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_artist.return_value = None

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient))
    info = await metadata_service.get_artist_info("Unknown")
    assert info is None
    mock_verifier.search_artist.assert_called_once_with("Unknown")


async def test_metadata_service_get_album_info_success(mock_metadata_verifier_cls):
    """Test successful fetching of album info."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_data = {
        "id": "456",
        "title": "Album",
        "first-release-date": "2024-01-01",
        "primary-type": "Album",
    }
    mock_verifier.search_album.return_value = mock_data

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient))
    info = await metadata_service.get_album_info("Artist", "Album")
    assert info is not None
    assert info["name"] == "Album"
    assert info["id"] == "456"
    assert info["source_name"] == "MusicBrainz"
    mock_verifier.search_album.assert_called_once_with("Artist", "Album")


async def test_metadata_service_get_album_info_not_found(mock_metadata_verifier_cls):
    """Test MetadataService when album info is not found."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_album.return_value = None

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient))
    info = await metadata_service.get_album_info("Artist", "Unknown")
    assert info is None
    mock_verifier.search_album.assert_called_once_with("Artist", "Unknown")


# --- Multi-Source Verification Tests (Adapted from old test file) ---

# Note: The original test for verify_track_version is now covered by test_metadata.py.
# We keep the fixtures for the old complex test cases that were failing due to the verifier change.


@pytest.fixture
def mock_mb_search():
    # Patch the async method from the newly refactored verifier
    with patch("backend.core.metadata.MetadataVerifier.search_recording") as mock:
        mock.return_value = AsyncMock()  # Ensure return value is awaitable
        yield mock


@pytest.fixture
def mock_discogs_search():
    # Patch the DiscogsClient instance used inside MetadataVerifier
    with patch("backend.core.metadata.DiscogsClient.search_track") as mock:
        mock.return_value = AsyncMock()  # Ensure return value is awaitable
        yield mock


async def test_verify_track_version_mb_exception(mock_mb_search, mock_discogs_search):
    """Test that if MusicBrainz raises an exception, we still try Discogs."""
    # We must mock the verifier's dependencies, not the verifier itself, to test its logic.
    # The actual verifier instance should be used here.
    with (
        patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()),
        patch("backend.core.metadata.settings.PROJECT_NAME", "VibomatTest"),
    ):

        verifier = MetadataVerifier(http_client=AsyncMock(spec=AsyncClient))

        # MB raises exception (simulate API call failure)
        mock_mb_search.side_effect = MusicBrainzAPIError("MB API failure")

        # Discogs should be called and succeed
        mock_discogs_search.return_value = "discogs:master:789"

        result = await verifier.verify_track_version("Artist", "Song", "studio")

        assert result is True
        mock_discogs_search.assert_called_once()


async def test_verify_track_version_both_fail_no_token(mock_mb_search):
    """Test that if MB fails and Discogs search fails, returns False."""
    with (
        patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()),
        patch("backend.core.metadata.DiscogsClient") as mock_discogs_cls,
    ):

        # Configure the mock DiscogsClient instance
        mock_discogs_client = AsyncMock(spec=DiscogsClient)
        mock_discogs_client.search_track.return_value = None  # Simulate Discogs failure
        mock_discogs_cls.return_value = mock_discogs_client

        verifier = MetadataVerifier(http_client=AsyncMock(spec=AsyncClient))

        # MB returns nothing
        mock_mb_search.return_value = []

        result = await verifier.verify_track_version("Artist", "Nonexistent Song", "studio")

    assert result is False
    mock_discogs_client.search_track.assert_called_once()
