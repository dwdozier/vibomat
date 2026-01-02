import pytest
import httpx
from unittest.mock import MagicMock, patch
from backend.app.main import app
from backend.app.models.user import User
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.api.v1.endpoints.users import get_metadata_service
from backend.app.services.metadata_service import MetadataService


@pytest.mark.asyncio
async def test_enrich_artist_success():
    """Test successful artist metadata enrichment."""
    mock_user = User(
        id="550e8400-e29b-41d4-a716-446655440000", email="user@example.com", is_active=True
    )
    mock_service = MagicMock()
    mock_service.get_artist_info.return_value = {
        "name": "Enriched Artist",
        "type": "Person",
        "country": "US",
    }

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_metadata_service] = lambda: mock_service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/profile/me/enrich/artist", json={"artist_name": "Artist"})
        assert response.status_code == 200
        assert response.json()["name"] == "Enriched Artist"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enrich_album_success():
    """Test successful album metadata enrichment."""
    mock_user = User(
        id="550e8400-e29b-41d4-a716-446655440000", email="user@example.com", is_active=True
    )
    mock_service = MagicMock()
    mock_service.get_album_info.return_value = {
        "name": "Enriched Album",
        "artist": "Artist",
        "first_release_date": "2020",
    }

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_metadata_service] = lambda: mock_service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/profile/me/enrich/album", json={"artist_name": "Artist", "album_name": "Album"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Enriched Album"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enrich_not_found():
    """Test enrichment failure (not found)."""
    mock_user = User(
        id="550e8400-e29b-41d4-a716-446655440000", email="user@example.com", is_active=True
    )
    mock_service = MagicMock()
    mock_service.get_artist_info.return_value = None

    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_metadata_service] = lambda: mock_service

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/v1/profile/me/enrich/artist", json={"artist_name": "Unknown"})
        assert res.status_code == 404

    app.dependency_overrides.clear()


def test_metadata_service_enrich_artist_none():
    """Test MetadataService when artist info is missing."""
    with patch("backend.app.services.metadata_service.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier_cls.return_value = mock_verifier
        mock_verifier.search_artist.return_value = None

        service = MetadataService()
        result = service.get_artist_info("Unknown")
        assert result is None


def test_metadata_service_enrich_album_none():
    """Test MetadataService when album info is missing."""
    with patch("backend.app.services.metadata_service.MetadataVerifier") as mock_verifier_cls:
        mock_verifier = MagicMock()
        mock_verifier_cls.return_value = mock_verifier
        mock_verifier.search_album.return_value = None

        service = MetadataService()
        result = service.get_album_info("Artist", "Unknown")
        assert result is None
