import pytest
from unittest.mock import MagicMock, patch
import os
from backend.core.ai import (
    get_ai_api_key,
    generate_playlist,
    list_available_models,
    discover_fallback_model,
)


def test_get_ai_api_key_env():
    """Test retrieving key from env."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_env_key"}):
        assert get_ai_api_key() == "test_env_key"


def test_get_ai_api_key_keyring():
    """Test retrieving key from keyring."""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = "test_keyring_key"

    with (
        patch.dict(os.environ, {}, clear=True),
        patch.dict("sys.modules", {"keyring": mock_keyring}),
    ):
        assert get_ai_api_key() == "test_keyring_key"


def test_get_ai_api_key_missing():
    """Test failure when key is missing."""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = None

    with (
        patch.dict(os.environ, {}, clear=True),
        patch.dict("sys.modules", {"keyring": mock_keyring}),
    ):
        with pytest.raises(ValueError, match="Gemini API Key not found"):
            get_ai_api_key()


def test_generate_playlist_success():
    """Test successful playlist generation with new SDK."""
    mock_response = MagicMock()
    mock_response.text = '[{"artist": "A", "track": "B"}]'

    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = generate_playlist("mood", 10)
        assert result == [{"artist": "A", "track": "B"}]
        mock_client.models.generate_content.assert_called_once()


def test_generate_playlist_json_cleanup():
    """Test that markdown code blocks are stripped."""
    mock_response = MagicMock()
    mock_response.text = '```json\n[{"artist": "A", "track": "B"}]\n```'

    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = generate_playlist("mood")
        assert result == [{"artist": "A", "track": "B"}]


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
        patch.dict(os.environ, {}, clear=True),  # Ensure no env var overrides
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
        assert (
            mock_client.models.generate_content.call_args_list[0][1]["model"]
            == "gemini-flash-latest"
        )
        # Second call with fallback
        assert mock_client.models.generate_content.call_args_list[1][1]["model"] == "fallback-model"


def test_generate_playlist_404_retry_same_model():
    """Test that we don't retry if fallback is same as initial model."""
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
        patch(
            "backend.core.ai.discover_fallback_model",
            return_value="gemini-flash-latest",
        ),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("404 Model not found")
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="404 Model not found"):
            generate_playlist("mood")

        # Should call discovery but NOT retry generation
        assert mock_client.models.generate_content.call_count == 1


def test_generate_playlist_dict_response():
    """Test generating a playlist where the AI returns a dict with 'tracks' key."""
    mock_response = MagicMock()
    mock_response.text = '{"tracks": [{"artist": "A", "track": "B"}]}'
    with (
        patch("backend.core.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        result = generate_playlist("mood")
        assert result == [{"artist": "A", "track": "B"}]


def test_verify_ai_tracks_success():
    """Test successful track verification."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T", "version": "studio"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier.verify_track_version.return_value = True
        mock_verifier_cls.return_value = mock_verifier

        verified, rejected = verify_ai_tracks(tracks)
        assert len(verified) == 1
        assert len(rejected) == 0


def test_verify_ai_tracks_rejected():
    """Test track verification with rejections."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier.verify_track_version.return_value = False
        mock_verifier_cls.return_value = mock_verifier

        verified, rejected = verify_ai_tracks(tracks)
        assert len(verified) == 0
        assert len(rejected) == 1
        assert rejected[0] == "A - T"


def test_verify_ai_tracks_exception():
    """Test track verification when the verifier raises an exception."""
    from backend.core.ai import verify_ai_tracks

    tracks = [{"artist": "A", "track": "T"}]
    with patch("backend.core.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier.verify_track_version.side_effect = Exception("MB Down")
        mock_verifier_cls.return_value = mock_verifier

        # We lean towards keeping tracks if verification fails technically
        verified, rejected = verify_ai_tracks(tracks)
        assert len(verified) == 1
        assert len(rejected) == 0
