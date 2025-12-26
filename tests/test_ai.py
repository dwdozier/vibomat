import pytest
from unittest.mock import MagicMock, patch
import os
from spotify_playlist_builder.ai import get_ai_api_key, generate_playlist, list_available_models


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


def test_verify_ai_tracks():
    """Test verification logic for AI tracks."""
    tracks = [
        {"artist": "Valid", "track": "Song", "version": "studio"},
        {"artist": "Invalid", "track": "Fake", "version": "studio"},
    ]

    with patch("spotify_playlist_builder.ai.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        # Mock first track as verified, second as rejected
        mock_verifier.verify_track_version.side_effect = [True, False]
        mock_verifier_cls.return_value = mock_verifier

        from spotify_playlist_builder.ai import verify_ai_tracks

        verified, rejected = verify_ai_tracks(tracks)

        assert len(verified) == 1
        assert verified[0]["artist"] == "Valid"
        assert len(rejected) == 1
        assert "Invalid - Fake" in rejected
