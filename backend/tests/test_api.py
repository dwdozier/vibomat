from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from backend.app.main import app
from backend.app.api.v1.endpoints.playlists import get_ai_service

client = TestClient(app)


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

    response = client.post("/api/v1/playlists/generate", json={"prompt": "fail"})

    assert response.status_code == 500
    assert response.json()["detail"] == "AI Error"

    app.dependency_overrides.clear()


def test_verify_tracks_error():
    """Test error handling in verification endpoint."""
    mock_service = MagicMock()
    mock_service.verify_tracks.side_effect = Exception("Verify Error")

    app.dependency_overrides[get_ai_service] = lambda: mock_service

    response = client.post(
        "/api/v1/playlists/verify", json={"tracks": [{"artist": "A", "track": "T"}]}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Verify Error"

    app.dependency_overrides.clear()


def test_get_ai_service_dependency():
    """Test the get_ai_service dependency function."""
    from backend.app.api.v1.endpoints.playlists import get_ai_service
    from backend.app.services.ai_service import AIService

    service = get_ai_service()
    assert isinstance(service, AIService)
