from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from backend.app.main import app
from backend.app.api.v1.endpoints.playlists import get_ai_service
from backend.app.core.auth.fastapi_users import current_active_user

client = TestClient(app)

# Helper to mock a user
mock_user = MagicMock()
mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
mock_user.email = "test@example.com"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_playlist_endpoint():
    """Test the AI generation endpoint."""
    mock_tracks = [{"artist": "Test Artist", "track": "Test Track", "version": "studio"}]
    mock_response_data = {
        "title": "Test Playlist",
        "description": "A test description",
        "tracks": mock_tracks,
    }

    expected_response = {
        "title": "Test Playlist",
        "description": "A test description",
        "tracks": [
            {
                "artist": "Test Artist",
                "track": "Test Track",
                "version": "studio",
                "album": None,
                "duration_ms": None,
                "uri": None,
            }
        ],
    }
    mock_service = MagicMock()
    mock_service.generate.return_value = mock_response_data

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post("/api/v1/playlists/generate", json={"prompt": "test prompt", "count": 1})

    assert response.status_code == 200
    assert response.json() == expected_response


def test_verify_tracks_endpoint():
    """Test the track verification endpoint."""
    mock_verified = [{"artist": "V", "track": "T", "version": "studio"}]
    expected_verified = [
        {
            "artist": "V",
            "track": "T",
            "version": "studio",
            "album": None,
            "duration_ms": None,
            "uri": None,
        }
    ]
    mock_rejected = ["R - S"]

    mock_service = MagicMock()
    mock_service.verify_tracks = AsyncMock(return_value=(mock_verified, mock_rejected))

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post(
        "/api/v1/playlists/verify",
        json={"tracks": [{"artist": "V", "track": "T"}, {"artist": "R", "track": "S"}]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["verified"] == expected_verified


def test_generate_playlist_error():
    """Test error handling in generation endpoint."""
    mock_service = MagicMock()
    mock_service.generate.side_effect = Exception("AI Error")

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post("/api/v1/playlists/generate", json={"prompt": "fail"})

    assert response.status_code == 500
    assert response.json()["detail"] == "AI Error"

    app.dependency_overrides.clear()


def test_verify_tracks_error():
    """Test error handling in verification endpoint."""
    mock_service = MagicMock()
    mock_service.verify_tracks = AsyncMock(side_effect=Exception("Verify Error"))

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post("/api/v1/playlists/verify", json={"tracks": [{"artist": "A", "track": "T"}]})

    assert response.status_code == 500
    assert response.json()["detail"] == "Verify Error"

    app.dependency_overrides.clear()


def test_spotify_login_endpoint():
    """Test the Spotify login redirect URL generation."""
    from backend.app.db.session import get_async_session
    from backend.app.core.config import settings

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    with patch.object(settings, "SPOTIFY_CLIENT_ID", "test_id"):
        response = client.get("/api/v1/integrations/spotify/login")
        assert response.status_code == 200
        assert "accounts.spotify.com/authorize" in response.json()["url"]
        assert "client_id=test_id" in response.json()["url"]

    app.dependency_overrides.clear()


def test_spotify_callback_endpoint():
    """Test the Spotify callback handling."""
    from backend.app.db.session import get_async_session
    from unittest.mock import AsyncMock
    from backend.app.core.config import settings

    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    # Mock the ServiceConnection lookup for credentials
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "acc",
        "refresh_token": "ref",
        "expires_in": 3600,
    }

    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"id": "spotify_id"}

    with (
        patch("httpx.AsyncClient.post", return_value=mock_token_resp),
        patch("httpx.AsyncClient.get", return_value=mock_user_resp),
        patch.object(settings, "SPOTIFY_CLIENT_ID", "test_id"),
        patch.object(settings, "SPOTIFY_CLIENT_SECRET", "test_secret"),
    ):

        response = client.get(
            f"/api/v1/integrations/spotify/callback?code=abc&state={mock_user.id}",
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert response.headers["location"] == "/settings"

    app.dependency_overrides.clear()


def test_spotify_callback_invalid_uuid():
    """Test Spotify callback with an invalid UUID string."""
    response = client.get("/api/v1/integrations/spotify/callback?code=abc&state=not-a-uuid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid state parameter (User ID)"


def test_spotify_callback_token_error_with_details():
    """Test Spotify callback handling when token exchange fails with details."""
    from backend.app.db.session import get_async_session
    from backend.app.core.config import settings

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 400
    mock_token_resp.json.return_value = {
        "error": "invalid_grant",
        "error_description": "Invalid code",
    }

    with (
        patch("httpx.AsyncClient.post", return_value=mock_token_resp),
        patch.object(settings, "SPOTIFY_CLIENT_ID", "test_id"),
        patch.object(settings, "SPOTIFY_CLIENT_SECRET", "test_secret"),
    ):
        response = client.get(f"/api/v1/integrations/spotify/callback?code=abc&state={mock_user.id}")
        assert response.status_code == 400
        assert "Invalid code" in response.json()["detail"]


def test_export_playlist_endpoint():
    """Test exporting a playlist to JSON."""
    payload = {
        "name": "Test Export",
        "description": "Desc",
        "tracks": [{"artist": "A", "track": "T"}],
    }
    app.dependency_overrides[current_active_user] = lambda: mock_user
    response = client.post("/api/v1/playlists/export", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["name"] == "Test Export"
    app.dependency_overrides.clear()


def test_build_playlist_endpoint_success():
    """Test successful playlist building on Spotify."""
    from backend.app.db.session import get_async_session
    from backend.app.models.service_connection import ServiceConnection
    from unittest.mock import AsyncMock

    mock_db = MagicMock()
    mock_conn = MagicMock(spec=ServiceConnection)
    mock_conn.access_token = "fake_token"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conn
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    payload = {
        "playlist_data": {
            "name": "Test Build",
            "description": "Desc",
            "public": False,
            "tracks": [{"artist": "A", "track": "T"}],
        }
    }

    with (
        patch("backend.app.api.v1.endpoints.playlists.SpotifyPlaylistBuilder") as mock_builder_cls,
        patch(
            "backend.app.api.v1.endpoints.playlists.IntegrationsService.get_valid_spotify_token",
            new_callable=AsyncMock,
        ) as mock_get_token,
    ):
        mock_get_token.return_value = "fake_token"
        mock_builder = MagicMock()
        mock_builder.create_playlist.return_value = "new_pid"
        mock_builder.add_tracks_to_playlist.return_value = ([], [])
        mock_builder_cls.return_value = mock_builder

        response = client.post("/api/v1/playlists/build", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["playlist_id"] == "new_pid"

    app.dependency_overrides.clear()


def test_build_playlist_endpoint_no_connection():
    """Test build failure when Spotify is not connected."""
    from backend.app.db.session import get_async_session

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    payload = {"playlist_data": {"name": "Test", "tracks": []}}
    response = client.post("/api/v1/playlists/build", json=payload)
    assert response.status_code == 400
    assert "Spotify relay station not connected" in response.json()["detail"]

    app.dependency_overrides.clear()

    app.dependency_overrides.clear()

    app.dependency_overrides.clear()

    app.dependency_overrides.clear()


def test_spotify_callback_existing_connection():
    """Test Spotify callback when a connection already exists."""
    from backend.app.db.session import get_async_session
    from backend.app.models.service_connection import ServiceConnection
    from unittest.mock import AsyncMock

    mock_db = MagicMock()
    mock_db.commit = AsyncMock()

    mock_conn = MagicMock(spec=ServiceConnection)
    mock_conn.credentials = {"client_id": "c", "client_secret": "s"}
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conn
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "acc",
        "refresh_token": "ref",
        "expires_in": 3600,
    }

    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"id": "spotify_id"}

    with (
        patch("httpx.AsyncClient.post", return_value=mock_token_resp),
        patch("httpx.AsyncClient.get", return_value=mock_user_resp),
    ):
        response = client.get(
            f"/api/v1/integrations/spotify/callback?code=abc&state={mock_user.id}",
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert response.headers["location"] == "/settings"

    app.dependency_overrides.clear()


def test_save_relay_config():
    """Test saving user-specific relay credentials."""
    from backend.app.db.session import get_async_session

    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    payload = {
        "provider": "spotify",
        "client_id": "custom_id",
        "client_secret": "custom_secret",
    }
    response = client.post("/api/v1/integrations/relay/config", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    app.dependency_overrides.clear()


def test_spotify_login_with_custom_creds():
    """Test spotify login uses custom credentials if available."""
    from backend.app.db.session import get_async_session
    from backend.app.models.service_connection import ServiceConnection

    mock_db = MagicMock()
    mock_conn = MagicMock(spec=ServiceConnection)
    mock_conn.credentials = {"client_id": "user_client_id"}
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conn
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.get("/api/v1/integrations/spotify/login")
    assert response.status_code == 200
    assert "user_client_id" in response.json()["url"]
    app.dependency_overrides.clear()


def test_build_playlist_endpoint_failure():
    """Test build failure handling in the endpoint."""
    from backend.app.db.session import get_async_session
    from backend.app.models.service_connection import ServiceConnection

    mock_db = MagicMock()
    mock_conn = MagicMock(spec=ServiceConnection)
    mock_conn.access_token = "fake_token"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conn
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_db
    app.dependency_overrides[current_active_user] = lambda: mock_user

    payload = {"playlist_data": {"name": "Fail", "tracks": []}}

    with (
        patch(
            "backend.app.api.v1.endpoints.playlists.SpotifyPlaylistBuilder",
            side_effect=Exception("Build Error"),
        ),
        patch(
            "backend.app.api.v1.endpoints.playlists.IntegrationsService.get_valid_spotify_token",
            new_callable=AsyncMock,
        ) as mock_get_token,
    ):
        mock_get_token.return_value = "fake_token"
        response = client.post("/api/v1/playlists/build", json=payload)
        assert response.status_code == 500
        assert "Failed to build playlist" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_get_ai_service_dependency():
    """Test the get_ai_service dependency function."""
    from backend.app.api.v1.endpoints.playlists import get_ai_service
    from backend.app.services.ai_service import AIService

    service = get_ai_service()
    assert isinstance(service, AIService)


def test_update_preferences_endpoint():
    """Test updating user preferences."""
    from backend.app.core.auth.fastapi_users import current_active_user

    # Mock current_active_user to bypass auth
    app.dependency_overrides[current_active_user] = lambda: MagicMock()

    response = client.patch(
        "/api/v1/profile/me/preferences",
        json={"discogs_pat": "test_token"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    app.dependency_overrides.clear()
