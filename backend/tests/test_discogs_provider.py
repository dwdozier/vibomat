from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from backend.core.providers.discogs import DiscogsClient, DiscogsAPIError


# Mock the internal httpx.AsyncClient to prevent real network calls
@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.AsyncClient used by DiscogsClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    # Mock the return value of httpx.AsyncClient on instantiation
    with patch("backend.core.providers.discogs.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


async def test_discogs_client_init_no_pat_raises_error():
    """Test that initialization fails if DISCOGS_PAT is missing."""
    with patch("backend.core.providers.discogs.settings.DISCOGS_PAT", None):
        with pytest.raises(ValueError) as excinfo:
            DiscogsClient()
        assert "DISCOGS_PAT is not configured" in str(excinfo.value)


async def test_search_track_success(mock_httpx_client):
    """Test successful track search using a mock API response."""
    # Mock the HTTP response object
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(
            return_value={
                "results": [
                    {
                        "id": 12345,
                        "type": "master",
                        "title": "Artist - Track Title",
                    }
                ]
            }
        ),
        raise_for_status=MagicMock(),
        text="mock response",
    )

    # Configure the mock client's get method to return the mock response
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()

    # 1. Test Red Phase: The current implementation will pass this test immediately
    # as it returns a mock value. I must ensure the implementation logic is correct.

    # Check current behavior (Green Phase - Test is expected to pass because implementation exists)
    result = await client.search_track(artist="The Band", track="The Song")

    # Assertions
    assert result == "discogs:master:12345"
    mock_httpx_client.get.assert_called_once()


async def test_search_track_not_found(mock_httpx_client):
    """Test case where no results are found."""
    # Mock the HTTP response object to return no results
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"results": []}),
        raise_for_status=MagicMock(),
        text="mock response",
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()
    result = await client.search_track(artist="Missing", track="Track")

    assert result is None
    mock_httpx_client.get.assert_called_once()


async def test_search_track_api_error(mock_httpx_client):
    """Test that a non-404 API error raises DiscogsAPIError."""
    # Mock the response to raise 403 Forbidden
    mock_response = MagicMock(status_code=403, text="Forbidden")
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden", request=httpx.Request("GET", "url"), response=mock_response
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()
    with pytest.raises(DiscogsAPIError) as excinfo:
        await client.search_track(artist="Error", track="Track")

    assert "403" in str(excinfo.value)
    mock_httpx_client.get.assert_called_once()
