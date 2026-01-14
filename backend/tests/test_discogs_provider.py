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
    assert result == {"uri": "discogs:master:12345"}
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


async def test_get_metadata_success(mock_httpx_client):
    """Test successful metadata retrieval for a Discogs master URI."""
    mock_response_payload = {
        "id": 12345,
        "title": "The Album",
        "artists": [{"name": "The Band"}],
        "year": 1970,
        "tracklist": [{"title": "The Song", "duration": "3:45", "position": "A1"}],
    }
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value=mock_response_payload),
        raise_for_status=MagicMock(),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()
    metadata = await client.get_metadata("discogs:master:12345")

    assert metadata is not None
    assert metadata["title"] == "The Album"
    assert metadata["artist"] == "The Band"
    assert metadata["year"] == 1970
    mock_httpx_client.get.assert_called_once_with("/masters/12345", params=None)


async def test_get_metadata_invalid_uri(mock_httpx_client):
    """Test that a malformed Discogs URI that causes a ValueError returns None."""
    client = DiscogsClient()
    # This URI will fail the "uri_type, uri_id = ..." unpacking
    result = await client.get_metadata("invalid-uri-no-colons")
    assert result is None
    mock_httpx_client.get.assert_not_called()


async def test_get_metadata_unsupported_uri_type(mock_httpx_client):
    """Test that an unsupported Discogs URI type returns None."""
    client = DiscogsClient()
    result = await client.get_metadata("discogs:album:12345")
    assert result is None
    mock_httpx_client.get.assert_not_called()


async def test_get_metadata_api_error(mock_httpx_client):
    """Test that a non-404 API error during metadata fetch raises DiscogsAPIError."""
    mock_response = MagicMock(status_code=500, text="Server Error")
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=httpx.Request("GET", "url"), response=mock_response
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()
    with pytest.raises(DiscogsAPIError):
        await client.get_metadata("discogs:master:12345")
    mock_httpx_client.get.assert_called_once()


async def test_get_metadata_no_artist(mock_httpx_client):
    """Test metadata retrieval when the response is missing artist information."""
    mock_response_payload = {"id": 12345, "title": "The Album", "year": 1970}
    mock_response = MagicMock(
        status_code=200,
        json=MagicMock(return_value=mock_response_payload),
        raise_for_status=MagicMock(),
    )
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = DiscogsClient()
    metadata = await client.get_metadata("discogs:release:12345")
    assert metadata is not None
    assert metadata["artist"] == "Unknown"


async def test_search_track_with_album(mock_httpx_client):
    """Test that the search query correctly includes the album."""
    mock_httpx_client.get = AsyncMock(
        return_value=MagicMock(status_code=200, json=MagicMock(return_value={"results": []}))
    )
    client = DiscogsClient()
    await client.search_track(artist="Artist", track="Track", album="Album")
    mock_httpx_client.get.assert_called_once()
    # Check that 'Album' is in the query parameter
    call_args = mock_httpx_client.get.call_args
    assert "Album" in call_args[1]["params"]["query"]


def test_retry_predicate_ignores_401():
    """Test the retry predicate correctly advises not to retry on 401."""
    from backend.core.providers.discogs import retry_if_not_auth_error

    # Should not retry
    exc_401 = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401))
    assert not retry_if_not_auth_error(exc_401)

    # Should retry
    exc_500 = httpx.HTTPStatusError("500 Error", request=MagicMock(), response=MagicMock(status_code=500))
    assert retry_if_not_auth_error(exc_500)
    assert retry_if_not_auth_error(ValueError("Some other error"))
