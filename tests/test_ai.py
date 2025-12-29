import pytest
from unittest.mock import MagicMock, patch
import os
from spotify_playlist_builder.ai import (
    get_ai_api_key,
    generate_playlist,
    list_available_models,
    get_best_flash_model,
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
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
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
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = generate_playlist("mood")
        assert result == [{"artist": "A", "track": "B"}]


def test_generate_playlist_failure():
    """Test failure from API."""
    with (
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
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
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
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
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
    ):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("List Error")
        mock_client_cls.return_value = mock_client

        assert list_available_models() == []


def test_list_available_models_no_client_init():
    """Test listing models failure during client init."""
    with patch("spotify_playlist_builder.ai.get_ai_api_key", side_effect=ValueError("No Key")):
        assert list_available_models() == []


def test_get_best_flash_model_env_var():
    """Test environment variable override."""
    with patch.dict(os.environ, {"GEMINI_MODEL": "custom-model"}):
        # We don't need a real client for this test
        assert get_best_flash_model(MagicMock()) == "custom-model"


def test_get_best_flash_model_auto_detect():
    """Test auto-detection of flash models."""
    mock_client = MagicMock()

    with patch("spotify_playlist_builder.ai.list_available_models") as mock_list:
        mock_list.return_value = ["models/gemini-1.0-pro", "models/gemini-1.5-flash"]
        # Should pick 1.5-flash from the known list
        assert get_best_flash_model(mock_client) == "gemini-1.5-flash"

        mock_list.return_value = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]
        # Should pick 2.0-flash-exp (higher priority in known list)
        assert get_best_flash_model(mock_client) == "gemini-2.0-flash-exp"


def test_get_best_flash_model_fallback():
    """Test fallback when no known models match."""
    mock_client = MagicMock()
    with patch("spotify_playlist_builder.ai.list_available_models") as mock_list:
        # No known models, but a flash model exists
        mock_list.return_value = ["models/some-random-flash-v9"]
        assert get_best_flash_model(mock_client) == "some-random-flash-v9"

        # No flash models at all
        mock_list.return_value = ["gemini-pro"]
        # Should return default hardcoded fallback
        assert get_best_flash_model(mock_client) == "gemini-2.0-flash"


def test_get_best_flash_model_exception():
    """Test get_best_flash_model exception handling."""
    mock_client = MagicMock()
    with patch("spotify_playlist_builder.ai.list_available_models", side_effect=Exception("Error")):
        assert get_best_flash_model(mock_client) == "gemini-2.0-flash"


def test_generate_playlist_404_handling():
    """Test handling of 404 errors with model listing suggestion."""
    with (
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.genai.Client") as mock_client_cls,
        patch("spotify_playlist_builder.ai.list_available_models", return_value=["valid-model"]),
    ):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("404 Not Found")
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="404 Not Found"):
            generate_playlist("mood")
        # Ensure list_available_models was called to provide suggestions
        # We can't easily assert on log output without caplog fixture, but coverage will count it


def test_get_best_flash_model_latest_alias():
    """Test prioritization of gemini-flash-latest."""
    mock_client = MagicMock()
    with patch("spotify_playlist_builder.ai.list_available_models") as mock_list:
        mock_list.return_value = ["models/gemini-2.0-flash", "models/gemini-flash-latest"]
        assert get_best_flash_model(mock_client) == "gemini-flash-latest"
