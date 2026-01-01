from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.app.main import app
from backend.app.api.v1.endpoints.playlists import get_ai_service
from backend.app.core.auth.fastapi_users import current_active_user

client = TestClient(app)

# Helper to mock a user
mock_user = MagicMock()
mock_user.id = "user_id"
mock_user.email = "test@example.com"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_playlist_endpoint():
    """Test the AI generation endpoint."""
    mock_tracks = [{"artist": "Test Artist", "track": "Test Track", "version": "studio"}]
    expected_response = [
        {"artist": "Test Artist", "track": "Test Track", "version": "studio", "album": None}
    ]

    mock_service = MagicMock()
    mock_service.generate.return_value = mock_tracks

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post("/api/v1/playlists/generate", json={"prompt": "test prompt", "count": 1})

    assert response.status_code == 200
    assert response.json() == expected_response
    mock_service.generate.assert_called_once_with(prompt="test prompt", count=1, artists=None)

    app.dependency_overrides.clear()


def test_verify_tracks_endpoint():
    """Test the track verification endpoint."""
    mock_verified = [{"artist": "V", "track": "T", "version": "studio"}]
    expected_verified = [{"artist": "V", "track": "T", "version": "studio", "album": None}]
    mock_rejected = ["R - S"]

    mock_service = MagicMock()
    mock_service.verify_tracks.return_value = (mock_verified, mock_rejected)

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post(
        "/api/v1/playlists/verify",
        json={"tracks": [{"artist": "V", "track": "T"}, {"artist": "R", "track": "S"}]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["verified"] == expected_verified
    assert data["rejected"] == mock_rejected

    app.dependency_overrides.clear()


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
    mock_service.verify_tracks.side_effect = Exception("Verify Error")

    app.dependency_overrides[get_ai_service] = lambda: mock_service
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.post(
        "/api/v1/playlists/verify", json={"tracks": [{"artist": "A", "track": "T"}]}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Verify Error"

    app.dependency_overrides.clear()


def test_spotify_login_endpoint():
    """Test the Spotify login redirect URL generation."""
    app.dependency_overrides[current_active_user] = lambda: mock_user

    response = client.get("/api/v1/integrations/spotify/login")
    assert response.status_code == 200
    assert "accounts.spotify.com/authorize" in response.json()["url"]

    app.dependency_overrides.clear()


def test_spotify_callback_endpoint():
    """Test the Spotify callback handling."""
    from backend.app.db.session import get_async_session
    from unittest.mock import AsyncMock

    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
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

        response = client.get("/api/v1/integrations/spotify/callback?code=abc&state=user_id")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    app.dependency_overrides.clear()


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
