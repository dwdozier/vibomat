import pytest
from unittest.mock import MagicMock, patch
from backend.core.providers.spotify import SpotifyProvider
from spotipy.exceptions import SpotifyException
from backend.core.client import SpotifyPlaylistBuilder
from datetime import datetime, timedelta, UTC
from backend.app.services.integrations_service import IntegrationsService
from backend.app.models.service_connection import ServiceConnection


@patch("backend.core.providers.spotify.spotipy.Spotify")
def test_spotify_provider_init_failure(mock_spotify_cls):
    """Test that SpotifyProvider handles initialization failure gracefully."""
    mock_spotify = MagicMock()
    mock_spotify_cls.return_value = mock_spotify

    # Simulate an expired token or other API error
    mock_spotify.current_user.side_effect = SpotifyException(401, -1, "The access token expired")

    provider = SpotifyProvider(auth_token="expired_token")
    with pytest.raises(SpotifyException) as excinfo:
        _ = provider.user_id

    assert excinfo.value.http_status == 401
    assert "The access token expired" in str(excinfo.value)


@patch("backend.core.client.spotipy.Spotify")
def test_spotify_builder_init_failure(mock_spotify_cls):
    """Test that SpotifyPlaylistBuilder handles initialization failure gracefully."""
    mock_spotify = MagicMock()
    mock_spotify_cls.return_value = mock_spotify

    # Simulate an expired token
    mock_spotify.current_user.return_value = None

    builder = SpotifyPlaylistBuilder(access_token="expired_token")
    with pytest.raises(Exception) as excinfo:
        _ = builder.user_id

    assert "Failed to authenticate with Spotify" in str(excinfo.value)


@patch("backend.core.providers.spotify.spotipy.Spotify")
def test_spotify_provider_init_success(mock_spotify_cls):
    """Test that SpotifyProvider initializes correctly with a valid token."""
    mock_spotify = MagicMock()
    mock_spotify_cls.return_value = mock_spotify
    mock_spotify.current_user.return_value = {"id": "test_user_id"}

    provider = SpotifyProvider(auth_token="valid_token")
    assert provider.user_id == "test_user_id"


@pytest.mark.asyncio
async def test_integrations_service_token_valid():
    """Test IntegrationsService returns existing token if not expired."""
    db = MagicMock()
    service = IntegrationsService(db)

    conn = ServiceConnection(
        access_token="valid_token", expires_at=datetime.now(UTC) + timedelta(hours=1)
    )

    token = await service.get_valid_spotify_token(conn)
    assert token == "valid_token"
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_integrations_service_token_refresh():
    """Test IntegrationsService refreshes token if expired."""
    db = MagicMock()

    # Mock async commit
    async def mock_commit():
        pass

    db.commit.side_effect = mock_commit

    service = IntegrationsService(db)

    conn = ServiceConnection(
        access_token="expired_token",
        refresh_token="refresh_me",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        credentials={"client_id": "cid", "client_secret": "csec"},
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600,
        "refresh_token": "new_refresh",
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        token = await service.get_valid_spotify_token(conn)

        assert token == "new_token"
        assert conn.access_token == "new_token"
        assert conn.refresh_token == "new_refresh"
        assert conn.expires_at > datetime.now(UTC)
        db.commit.assert_called_once()

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["refresh_token"] == "refresh_me"
        assert kwargs["data"]["client_id"] == "cid"


@pytest.mark.asyncio
async def test_integrations_service_token_refresh_no_refresh_token():
    """Test token refresh fails if no refresh token available."""
    db = MagicMock()
    service = IntegrationsService(db)

    conn = ServiceConnection(
        access_token="expired",
        refresh_token=None,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )

    with pytest.raises(Exception) as exc:
        await service.get_valid_spotify_token(conn)
    assert "No refresh token available" in str(exc.value)


@pytest.mark.asyncio
async def test_integrations_service_token_refresh_no_creds():
    """Test token refresh fails if no credentials available."""
    db = MagicMock()
    service = IntegrationsService(db)

    # For now, let's test the path where credentials dict is present but empty keys
    conn = ServiceConnection(
        access_token="expired",
        refresh_token="ref",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        credentials={},
    )

    with (
        patch("backend.app.services.integrations_service.DEFAULT_SPOTIFY_CLIENT_ID", None),
        patch("backend.app.services.integrations_service.DEFAULT_SPOTIFY_CLIENT_SECRET", None),
    ):

        with pytest.raises(Exception) as exc:
            await service.get_valid_spotify_token(conn)
        assert "Spotify Relay credentials not found" in str(exc.value)


@pytest.mark.asyncio
async def test_integrations_service_token_refresh_api_error():
    """Test token refresh handles API errors."""
    db = MagicMock()
    service = IntegrationsService(db)

    conn = ServiceConnection(
        access_token="expired",
        refresh_token="ref",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        credentials={"client_id": "cid", "client_secret": "cs"},
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": "invalid_grant", "error_description": "Bad token"}

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(Exception) as exc:
            await service.get_valid_spotify_token(conn)
        assert "Failed to refresh Spotify token" in str(exc.value)
        assert "Bad token" in str(exc.value)
