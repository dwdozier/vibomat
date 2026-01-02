from unittest.mock import patch, MagicMock
from backend.app.services.ai_service import AIService
from backend.app.services.metadata_service import MetadataService


def test_ai_service_generate():
    service = AIService()
    with patch("backend.app.services.ai_service.generate_playlist") as mock_gen:
        mock_gen.return_value = [{"artist": "A", "track": "T"}]
        result = service.generate("prompt", 10, "artists")
        assert result == [{"artist": "A", "track": "T"}]
        mock_gen.assert_called_once_with("prompt. Inspired by artists: artists", 10)


def test_ai_service_verify():
    service = AIService()
    with patch("backend.app.services.ai_service.verify_ai_tracks") as mock_verify:
        mock_verify.return_value = ([], [])
        result = service.verify_tracks([{"artist": "A"}])
        assert result == ([], [])
        mock_verify.assert_called_once_with([{"artist": "A"}])


def test_metadata_service_enrich_artist():
    with patch("backend.app.services.metadata_service.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier_cls.return_value = mock_verifier
        mock_verifier.search_artist.return_value = {"name": "Enriched", "id": "123"}

        service = MetadataService()
        result = service.get_artist_info("Artist")

        assert result is not None
        assert result["name"] == "Enriched"
        mock_verifier.search_artist.assert_called_once_with("Artist")


def test_metadata_service_enrich_album():
    with patch("backend.app.services.metadata_service.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier_cls.return_value = mock_verifier
        mock_verifier.search_album.return_value = {"title": "Album", "id": "456"}

        service = MetadataService()
        result = service.get_album_info("Artist", "Album")

        assert result is not None
        assert result["name"] == "Album"
        mock_verifier.search_album.assert_called_once_with("Artist", "Album")
