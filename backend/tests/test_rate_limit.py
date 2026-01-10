import pytest
from spotipy.exceptions import SpotifyException


@pytest.mark.ci
def test_rate_limit_retry_success(builder, mock_spotify):
    """
    Test that a method decorated with @rate_limit_retry retries on 429.
    """
    # Simulate a 429 error followed by success
    rate_limit_exception = SpotifyException(429, -1, "Too Many Requests", headers={"Retry-After": "0"})

    # We'll use search_track as the test subject
    mock_spotify.search.side_effect = [
        rate_limit_exception,
        {
            "tracks": {
                "items": [
                    {
                        "uri": "spotify:track:123",
                        "name": "Track",
                        "artists": [{"name": "Artist"}],
                        "album": {"name": "Album"},
                    }
                ]
            }
        },
    ]

    # Call the method
    uri = builder.search_track("Artist", "Track")

    # Assertions
    assert uri == "spotify:track:123"
    # search should have been called twice (1 failure + 1 success)
    assert mock_spotify.search.call_count == 2


@pytest.mark.ci
def test_rate_limit_retry_failure(builder, mock_spotify):
    """
    Test that retries eventually stop and raise the exception.
    """
    rate_limit_exception = SpotifyException(429, -1, "Too Many Requests", headers={"Retry-After": "0"})

    # Always raise 429
    mock_spotify.search.side_effect = rate_limit_exception

    # We expect it to fail after retries (configured to 5 attempts)
    with pytest.raises(SpotifyException) as exc:
        builder.search_track("Artist", "Track")

    assert exc.value.http_status == 429
    # Should have been called 5 times (1 initial + 4 retries)
    assert mock_spotify.search.call_count == 5


@pytest.mark.ci
def test_other_exception_no_retry(builder, mock_spotify):
    """
    Test that other exceptions are NOT retried.
    """
    other_exception = SpotifyException(500, -1, "Server Error", headers={})

    mock_spotify.search.side_effect = other_exception

    with pytest.raises(SpotifyException) as exc:
        builder.search_track("Artist", "Track")

    assert exc.value.http_status == 500
    # Should be called only once
    assert mock_spotify.search.call_count == 1
