import json
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import httpx
from backend.core.ai import (
    get_ai_api_key,
    generate_playlist,
    list_available_models,
    discover_fallback_model,
)
from backend.core.metadata import MetadataVerifier
from backend.app.core.config import settings
from backend.core.providers.spotify import SpotifyProvider


def test_get_ai_api_key_env():
    """Test retrieving key from env."""
    with patch.object(settings, "GEMINI_API_KEY", "test_env_key"):
        assert get_ai_api_key() == "test_env_key"


def test_get_ai_api_key_missing():
    """Test failure when key is missing."""
    with patch.object(settings, "GEMINI_API_KEY", None):
        with pytest.raises(ValueError, match="Gemini API Key not found"):
            get_ai_api_key()


def test_generate_playlist_success():
    """Test successful playlist generation."""
    mock_response = MagicMock()
    # Updated to new JSON schema
    mock_response.text = json.dumps(
        {
            "title": "My Playlist",
            "description": "Desc",
            "tracks": [
                {
                    "artist": "Artist 1",
                    "track": "Track 1",
                    "version": "studio",
                    "duration_ms": 180000,
                }
            ],
        }
    )

    with (
        patch("backend.core.ai.genai.Client"),
        patch("backend.core.ai.get_ai_api_key", return_value="fake_key"),
        patch("backend.core.ai.generate_content_with_retry", return_value=mock_response),
    ):
        result = generate_playlist("test prompt")
        assert result["title"] == "My Playlist"
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["artist"] == "Artist 1"
        assert result["tracks"][0]["duration_ms"] == 180000


def test_generate_playlist_json_cleanup():
    """Test that markdown code blocks are stripped."""
    mock_response = MagicMock()
    mock_response.text = '```json\n{"tracks": [{"artist": "A", "track": "B"}]}\n```'

    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = generate_playlist("mood")
        assert result["tracks"] == [{"artist": "A", "track": "B"}]


def test_generate_playlist_failure():
    """Test failure from API (non-404)."""
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="API Error"):
            generate_playlist("mood")


def test_list_available_models():
    """Test listing available models."""
    mock_model = MagicMock()
    mock_model.name = "models/gemini-1.5-flash"
    mock_model.supported_generation_methods = ["generateContent"]

    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.list.return_value = [mock_model]
        mock_client_cls.return_value = mock_client

        models = list_available_models()
        assert "models/gemini-1.5-flash" in models


def test_list_available_models_failure():
    """Test listing models failure."""
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("List Error")
        mock_client_cls.return_value = mock_client

        assert list_available_models() == []


def test_list_available_models_no_client_init():
    """Test listing models failure during client init."""
    with patch("backend.core.ai.get_ai_api_key", side_effect=ValueError("No Key")):
        assert list_available_models() == []


def test_discover_fallback_model_dynamic():
    """Test dynamic discovery of fallback models."""
    mock_client = MagicMock()

    with patch("backend.core.ai.list_available_models") as mock_list:
        # 1. Standard sort (gemini-2.0 > gemini-1.5)
        mock_list.return_value = ["gemini-1.5-flash", "gemini-2.0-flash"]
        assert discover_fallback_model(mock_client) == "gemini-2.0-flash"

        # 2. Version sort (002 > 001)
        mock_list.return_value = ["gemini-1.5-flash-001", "gemini-1.5-flash-002"]
        assert discover_fallback_model(mock_client) == "gemini-1.5-flash-002"

        # 3. Random flash model
        mock_list.return_value = ["models/some-random-flash-v9"]
        assert discover_fallback_model(mock_client) == "some-random-flash-v9"


def test_discover_fallback_model_fallback():
    """Test fallback when no flash models match."""
    mock_client = MagicMock()
    with patch("backend.core.ai.list_available_models") as mock_list:
        mock_list.return_value = ["gemini-pro"]
        assert discover_fallback_model(mock_client) == "gemini-2.0-flash"


def test_discover_fallback_model_exception():
    """Test discover_fallback_model exception handling."""
    mock_client = MagicMock()
    with patch("backend.core.ai.list_available_models", side_effect=Exception("Error")):
        assert discover_fallback_model(mock_client) == "gemini-2.0-flash"


def test_generate_playlist_404_retry():
    """Test that generation retries with a discovered fallback model on 404."""
    mock_response = MagicMock()
    mock_response.text = "[]"

    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
        patch("backend.core.ai.discover_fallback_model", return_value="fallback-model"),
        patch.object(settings, "GEMINI_MODEL", "gemini-flash-latest"),
    ):
        mock_client = MagicMock()
        # First call fails, Second call succeeds
        mock_client.models.generate_content.side_effect = [
            Exception("404 Model not found"),
            mock_response,
        ]
        mock_client_cls.return_value = mock_client

        generate_playlist("mood")

        assert mock_client.models.generate_content.call_count == 2
        # First call with default
        assert mock_client.models.generate_content.call_args_list[0].kwargs["model"] == "gemini-flash-latest"
        # Second call with fallback
        assert mock_client.models.generate_content.call_args_list[1].kwargs["model"] == "fallback-model"


def test_generate_playlist_404_retry_same_model():
    """Test that we don't retry if fallback is same as initial model."""
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
        patch(
            "backend.core.ai.discover_fallback_model",
            return_value="gemini-flash-latest",
        ),
        patch.object(settings, "GEMINI_MODEL", "gemini-flash-latest"),
    ):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("404 Model not found")
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="404 Model not found"):
            generate_playlist("mood")

        # Should call discovery but NOT retry generation
        assert mock_client.models.generate_content.call_count == 1


def test_generate_playlist_legacy_list_support():
    """Test that legacy list responses are wrapped in a dict."""
    mock_response = MagicMock()
    mock_response.text = '[{"artist": "A", "track": "B"}]'
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        result = generate_playlist("mood")
        assert result["title"] == "AI Playlist"
        assert result["tracks"] == [{"artist": "A", "track": "B"}]


@pytest.fixture
def async_mock_client():
    """Mocks the httpx.AsyncClient for MetadataVerifier."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def mock_spotify_provider():
    """Mocks the SpotifyProvider."""
    return AsyncMock(spec=SpotifyProvider)


async def test_verify_ai_tracks_success(async_mock_client, mock_spotify_provider):
    """Test successful track verification."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T", "version": "studio"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        # search_recording is async, but we patch verifier class here.
        # It's safest to set the return value to an awaitable mock
        mock_verifier.verify_track_version.return_value = AsyncMock(return_value=True)
        mock_verifier_cls.return_value = mock_verifier

        verified, rejected = await verify_ai_tracks(
            tracks,
            http_client=async_mock_client,
            spotify_provider=mock_spotify_provider,
        )

        assert verified == tracks
        assert rejected == []
        mock_verifier_cls.assert_called_once_with(http_client=async_mock_client, spotify_provider=mock_spotify_provider)
        mock_verifier.verify_track_version.assert_called_once_with("A", "T", "studio")


async def test_verify_ai_tracks_rejected(async_mock_client, mock_spotify_provider):
    """Test track verification with rejections."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = AsyncMock(spec=MetadataVerifier)
        mock_verifier.verify_track_version.return_value = False
        mock_verifier_cls.return_value = mock_verifier
        verified, rejected = await verify_ai_tracks(
            tracks,
            http_client=async_mock_client,
            spotify_provider=mock_spotify_provider,
        )

        assert verified == []
        assert rejected == ["A - T"]
        mock_verifier_cls.assert_called_once_with(http_client=async_mock_client, spotify_provider=mock_spotify_provider)


async def test_verify_ai_tracks_exception(async_mock_client, mock_spotify_provider):
    """Test track verification when the verifier raises an exception."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier.verify_track_version.side_effect = Exception("MB Down")
        mock_verifier_cls.return_value = mock_verifier

        # We lean towards keeping tracks if verification fails technically
        verified, rejected = await verify_ai_tracks(
            tracks,
            http_client=async_mock_client,
            spotify_provider=mock_spotify_provider,
        )

        assert verified == tracks
        assert rejected == []
