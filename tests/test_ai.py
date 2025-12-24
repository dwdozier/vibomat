import pytest
from unittest.mock import MagicMock, patch
import os
from spotify_playlist_builder.ai import get_ai_api_key, generate_playlist


def test_get_ai_api_key_env():
    """Test retrieving key from env."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_env_key"}):
        assert get_ai_api_key() == "test_env_key"


def test_get_ai_api_key_keyring():
    """Test retrieving key from keyring."""
    # We must patch sys.modules if keyring is imported inside the function,
    # OR since get_ai_api_key does 'import keyring', we can patch 'keyring' if it's already in
    # sys.modules or use patch.dict('sys.modules', ...)

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
    """Test successful playlist generation."""
    mock_response = MagicMock()
    mock_response.text = '[{"artist": "A", "track": "B"}]'

    with (
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.generativeai.GenerativeModel") as mock_model_cls,
    ):

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        result = generate_playlist("mood", 10)
        assert result == [{"artist": "A", "track": "B"}]
        mock_model.generate_content.assert_called_once()


def test_generate_playlist_json_cleanup():
    """Test that markdown code blocks are stripped."""
    mock_response = MagicMock()
    mock_response.text = '```json\n[{"artist": "A", "track": "B"}]\n```'

    with (
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.generativeai.GenerativeModel") as mock_model_cls,
    ):

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        result = generate_playlist("mood")
        assert result == [{"artist": "A", "track": "B"}]


def test_generate_playlist_failure():
    """Test failure from API."""
    with (
        patch("spotify_playlist_builder.ai.get_ai_api_key", return_value="key"),
        patch("google.generativeai.GenerativeModel") as mock_model_cls,
    ):

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_cls.return_value = mock_model

        with pytest.raises(Exception, match="API Error"):
            generate_playlist("mood")
