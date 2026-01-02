import pytest
from unittest.mock import MagicMock, patch
from backend.core.ai import generate_playlist
from backend.app.services.ai_service import AIService


@pytest.fixture
def mock_genai_client():
    with patch("backend.core.ai.genai.Client") as mock:
        yield mock


def test_generate_playlist_prompt_structure(mock_genai_client):
    """Test that the prompt includes the description and count."""
    mock_response = MagicMock()
    mock_response.text = '[{"artist": "A", "track": "T", "version": "studio", "duration_ms": 1000}]'
    mock_genai_client.return_value.models.generate_content.return_value = mock_response

    with patch("backend.core.ai.get_ai_api_key", return_value="fake_key"):
        generate_playlist("test description", count=10)

    call_args = mock_genai_client.return_value.models.generate_content.call_args
    assert call_args is not None
    contents = call_args.kwargs["contents"]
    user_message = contents[1]
    assert "test description" in user_message
    assert "generate exactly 10 tracks" in user_message


def test_generate_playlist_fallback_logic(mock_genai_client):
    """Test that the system falls back to a discovered model on 404."""
    # First call raises 404 (non-retryable for retry decorator, but handled in loop?)
    # Wait, code logic:
    # try: generate... except Exception as e: if not is_retryable(e): attempt fallback

    error_404 = Exception("404 Not Found")

    mock_client_instance = mock_genai_client.return_value

    # Mock list models for discovery
    mock_model = MagicMock()
    mock_model.name = "models/gemini-1.5-flash"
    mock_model.supported_generation_methods = ["generateContent"]
    mock_client_instance.models.list.return_value = [mock_model]

    # Side effect: first call raises 404, second call returns success
    mock_response = MagicMock()
    mock_response.text = "[]"

    mock_client_instance.models.generate_content.side_effect = [error_404, mock_response]

    with patch("backend.core.ai.get_ai_api_key", return_value="fake_key"):
        generate_playlist("desc")

        # Verify fallback model was used in second call

        assert mock_client_instance.models.generate_content.call_count == 2

        args2 = mock_client_instance.models.generate_content.call_args_list[1]

        # First call used default (from env or hardcoded)

    # Second call should use "gemini-1.5-flash" (discovered)
    assert args2.kwargs["model"] == "gemini-1.5-flash"


def test_ai_service_full_prompt_construction():
    """Test that AIService constructs the prompt correctly with artists."""
    service = AIService()
    with patch("backend.app.services.ai_service.generate_playlist") as mock_gen:
        service.generate("my prompt", count=5, artists="Pink Floyd")

    mock_gen.assert_called_once()
    args, kwargs = mock_gen.call_args
    assert "my prompt. Inspired by artists: Pink Floyd" in args[0]
