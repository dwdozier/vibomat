import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.metadata import MetadataVerifier, MusicBrainzAPIError
from backend.core.providers.discogs import DiscogsClient
from httpx import AsyncClient, RequestError, HTTPStatusError
import asyncio

# --- Fixtures ---


@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.AsyncClient used by MetadataVerifier."""
    mock_client = AsyncMock(spec=AsyncClient)
    # The verifier expects an AsyncClient to be passed in, so we just mock its get method
    yield mock_client


@pytest.fixture
def mock_discogs_client():
    """Mocks the DiscogsClient used by MetadataVerifier."""
    mock_client = AsyncMock(spec=DiscogsClient)
    with patch("backend.core.metadata.DiscogsClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def verifier(mock_httpx_client, mock_discogs_client):
    """Asynchronous fixture for the MetadataVerifier."""
    return MetadataVerifier(http_client=mock_httpx_client)


@pytest.fixture(autouse=True)
def mock_discogs_pat():
    """Ensure DiscogsClient can be initialized in the verifier."""
    with patch("backend.core.providers.discogs.settings.DISCOGS_PAT", "mock-pat"):
        yield


# --- MusicBrainz Tests ---


async def test_search_recording_success(verifier, mock_httpx_client):
    """Test successful search for a recording via MusicBrainz."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"recordings": [{"title": "Test Song", "id": "123"}]}),
        text="mock",
    )
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    results = await verifier.search_recording("Artist", "Track")

    assert results == [{"title": "Test Song", "id": "123"}]
    mock_httpx_client.get.assert_called_once()
    assert "https://musicbrainz.org/ws/2/recording" in mock_httpx_client.get.call_args.args[0]


async def test_search_recording_api_error(verifier, mock_httpx_client):
    """Test handling of MusicBrainz API errors (non-4xx, non-404, causing retry)."""
    # Mocking a transient RequestError which tenacity should retry
    mock_httpx_client.get.side_effect = [
        RequestError("Transient error"),
        RequestError("Transient error"),
        RequestError("Transient error"),
    ]

    with pytest.raises(RequestError):
        await verifier.search_recording("Artist", "Track")

    assert mock_httpx_client.get.call_count == 3


async def test_search_recording_http_status_error(verifier, mock_httpx_client):
    """Test handling of MusicBrainz HTTP status errors (e.g., 500)."""
    mock_response = MagicMock(status_code=500, text="Server Error")
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        "500 Internal Server Error", request=AsyncMock(), response=mock_response
    )
    mock_httpx_client.get.return_value = mock_response

    with pytest.raises(MusicBrainzAPIError) as excinfo:
        await verifier.search_recording("Artist", "Track")

    assert "500" in str(excinfo.value)


async def test_search_recording_unexpected_error(verifier, mock_httpx_client):
    """Test handling of unexpected errors (json parsing failure)."""
    mock_response = MagicMock(status_code=200)
    mock_response.json.side_effect = ValueError("JSON Error")
    mock_httpx_client.get.return_value = mock_response

    results = await verifier.search_recording("Artist", "Track")
    assert results == []


# --- Search/Verify Tests ---


async def test_verify_track_version_default(verifier, mock_httpx_client):
    """Test verification checks MB API for default/studio version."""
    # Mock MB response
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"recordings": [{"title": "Song", "disambiguation": ""}]}),
        text="mock",
    )
    mock_httpx_client.get.return_value = mock_response

    # Patch asyncio.sleep for rate limit enforcement
    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        assert await verifier.verify_track_version("Artist", "Track", "studio") is True
        assert await verifier.verify_track_version("Artist", "Track", None) is True

    # Should be called once for each search
    assert mock_httpx_client.get.call_count == 2


async def test_verify_track_version_live_match(verifier, mock_httpx_client):
    """Test verification for live version match."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(
            return_value={
                "recordings": [
                    {"title": "Song", "disambiguation": "Studio"},
                    {"title": "Song (Live)", "disambiguation": "Live at Venue"},
                ]
            }
        ),
        text="mock",
    )
    mock_httpx_client.get.return_value = mock_response

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        assert await verifier.verify_track_version("Artist", "Song", "live") is True


async def test_verify_track_version_no_match_fallback_fail(verifier, mock_httpx_client, mock_discogs_client):
    """Test verification returns False when MB fails and Discogs fails."""
    # 1. MB Fails to find version
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"recordings": [{"title": "Song", "disambiguation": ""}]}),
        text="mock",
    )
    mock_httpx_client.get.return_value = mock_response

    # 2. Discogs Fails (returns None)
    mock_discogs_client.search_track.return_value = None

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.verify_track_version("Artist", "Song", "live")

    assert result is False
    mock_httpx_client.get.assert_called_once()
    mock_discogs_client.search_track.assert_called_once()


# --- Multi-Source (Discogs Fallback) Tests ---


async def test_verify_track_mb_fail_discogs_success(verifier, mock_httpx_client, mock_discogs_client):
    """Test that if MusicBrainz finds nothing, Discogs is called and succeeds."""
    # 1. MB Fails (returns empty list)
    mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"recordings": []}), text="mock")
    mock_httpx_client.get.return_value = mock_response

    # 2. Discogs Succeeds (returns a URI)
    mock_discogs_client.search_track.return_value = "discogs:master:123"

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.verify_track_version("Artist", "Test Song", "studio")

    assert result is True
    mock_httpx_client.get.assert_called_once()
    mock_discogs_client.search_track.assert_called_once()


async def test_verify_track_mb_http_error_discogs_success(verifier, mock_httpx_client, mock_discogs_client):
    """Test that if MusicBrainz throws an HTTP error, Discogs is called and succeeds."""
    # 1. MB Throws 400 Bad Request (MusicBrainzAPIError)
    mock_response = MagicMock(status_code=400, text="Bad Request")
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        "400 Bad Request", request=AsyncMock(), response=mock_response
    )
    mock_httpx_client.get.return_value = mock_response

    # 2. Discogs Succeeds (returns a URI)
    mock_discogs_client.search_track.return_value = "discogs:master:456"

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.verify_track_version("Artist", "Test Song", "studio")

    assert result is True
    mock_discogs_client.search_track.assert_called_once()


# --- Async Utility Tests ---


async def test_metadata_verifier_rate_limit(verifier):
    """Test the asynchronous rate limit enforcement in MetadataVerifier."""
    verifier.last_request_time = asyncio.get_event_loop().time() - 0.1  # 100ms ago

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        # This will trigger the sleep branch logic because 0.1 < 1.1
        await verifier._enforce_rate_limit()
        mock_sleep.assert_called_once()
        # Verify sleep duration is roughly correct (1.1 - 0.1 = 1.0)
        assert mock_sleep.call_args[0][0] == pytest.approx(1.0, abs=0.01)


# --- Other Search Methods ---


async def test_search_artist_success(verifier, mock_httpx_client):
    """Test successful artist search."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"artists": [{"name": "Test Artist", "id": "123"}]}),
        text="mock",
    )
    mock_httpx_client.get.return_value = mock_response

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.search_artist("Test Artist")

    assert result["name"] == "Test Artist"


async def test_search_album_success(verifier, mock_httpx_client):
    """Test successful album search."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"release-groups": [{"title": "Test Album", "id": "456"}]}),
        text="mock",
    )
    mock_httpx_client.get.return_value = mock_response

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.search_album("Artist", "Album")

    assert result["title"] == "Test Album"


async def test_verify_track_version_remaster(verifier, mock_httpx_client):
    """Test verification for remastered version match."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(
            return_value={
                "recordings": [
                    {"title": "Song (2024 Remaster)", "disambiguation": "Remastered"},
                ]
            }
        ),
    )
    mock_httpx_client.get.return_value = mock_response

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        assert await verifier.verify_track_version("Artist", "Song", "remaster") is True


async def test_verify_track_version_remix(verifier, mock_httpx_client):
    """Test verification for remix version match."""
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(
            return_value={
                "recordings": [
                    {"title": "Song (Radio Mix)", "disambiguation": "Remix"},
                ]
            }
        ),
    )
    mock_httpx_client.get.return_value = mock_response

    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        assert await verifier.verify_track_version("Artist", "Song", "remix") is True


async def test_search_artist_error_edge(verifier, mock_httpx_client):
    """Test search_artist with an error during request."""
    mock_httpx_client.get.side_effect = Exception("Artist search failed")
    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.search_artist("Artist")
    assert result is None


async def test_search_album_error_edge(verifier, mock_httpx_client):
    """Test search_album with an error during request."""
    mock_httpx_client.get.side_effect = Exception("Album search failed")
    with patch("backend.core.metadata.asyncio.sleep", new=AsyncMock()):
        result = await verifier.search_album("Artist", "Album")
    assert result is None
