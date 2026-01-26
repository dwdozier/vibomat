from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import uuid
from datetime import datetime, timedelta, UTC
from httpx import AsyncClient, Response
from backend.core.metadata import MetadataVerifier
from backend.core.providers.spotify import SpotifyProvider

from backend.app.services.metadata_service import MetadataService
from backend.app.services.integrations_service import IntegrationsService
from backend.app.services.ai_service import AIService
from backend.app.models.ai_log import AIInteractionEmbedding
from backend.app.models.service_connection import ServiceConnection
from backend.app.exceptions import TokenRefreshError, SpotifyAPIError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.AsyncClient to be passed to MetadataService."""
    mock_client = AsyncMock(spec=AsyncClient)
    yield mock_client


@pytest.fixture
def mock_spotify_provider():
    """Mocks the SpotifyProvider."""
    return AsyncMock(spec=SpotifyProvider)


@pytest.fixture
def mock_metadata_verifier_cls():
    """Mocks the MetadataVerifier class to track instantiations and methods."""
    with patch("backend.app.services.metadata_service.MetadataVerifier", spec=MetadataVerifier) as mock_cls:
        mock_instance = AsyncMock(spec=MetadataVerifier)
        mock_cls.return_value = mock_instance
        yield mock_cls


@pytest.fixture
def metadata_service(mock_httpx_client, mock_spotify_provider):
    """Fixture to instantiate MetadataService with a mock client."""
    return MetadataService(http_client=mock_httpx_client, spotify_provider=mock_spotify_provider)


async def test_metadata_service_enrich_artist(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful artist enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_artist.return_value = {"name": "Enriched", "id": "123"}

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_artist_info("Artist")
    assert result is not None
    assert result["name"] == "Enriched"
    mock_verifier.search_artist.assert_called_once_with("Artist")


async def test_metadata_service_enrich_album(mock_metadata_verifier_cls, mock_spotify_provider):
    """Test successful album enrichment."""
    mock_verifier = mock_metadata_verifier_cls.return_value
    mock_verifier.search_album.return_value = {"title": "Album", "id": "456"}

    metadata_service = MetadataService(http_client=AsyncMock(spec=AsyncClient), spotify_provider=mock_spotify_provider)
    result = await metadata_service.get_album_info("Artist", "Album")
    assert result is not None
    assert result["name"] == "Album"
    mock_verifier.search_album.assert_called_once_with("Artist", "Album")


def test_integrations_service_init():
    """Test that IntegrationsService initializes correctly."""
    service = IntegrationsService(db=MagicMock())
    assert service.db is not None


@pytest.mark.asyncio
async def test_store_interaction_embedding():
    mock_db = AsyncMock(spec=AsyncSession)
    service = AIService(db=mock_db)

    user_id = "test-user"
    prompt = "Test prompt"
    embedding = [0.1, 0.2, 0.3]

    result = await service.store_interaction_embedding(user_id, prompt, embedding)

    assert isinstance(result, AIInteractionEmbedding)
    assert result.user_id == user_id
    assert result.prompt == prompt
    assert result.embedding == embedding
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_store_interaction_no_db():
    service = AIService(db=None)
    with pytest.raises(ValueError, match="Database session required"):
        await service.store_interaction_embedding("user", "prompt", [])


@pytest.mark.asyncio
async def test_get_nearest_interactions():
    mock_db = AsyncMock(spec=AsyncSession)
    service = AIService(db=mock_db)

    # Mocking the result of the query
    mock_interaction = MagicMock(spec=AIInteractionEmbedding)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_interaction]
    mock_db.execute.return_value = mock_result

    embedding = [0.1, 0.2, 0.3]
    results = await service.get_nearest_interactions(embedding, limit=5)

    assert len(results) == 1
    assert results[0] == mock_interaction
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_nearest_interactions_no_db():
    service = AIService(db=None)
    with pytest.raises(ValueError, match="Database session required"):
        await service.get_nearest_interactions([])


class TestTokenRefresh:
    """Test token refresh functionality with locking."""

    @pytest.mark.asyncio
    async def test_valid_token_no_refresh(self):
        """Test that valid token is returned without refresh."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        service = IntegrationsService(db=mock_db, redis=mock_redis)

        # Create connection with valid token (expires in future)
        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.provider_name = "spotify"
        connection.provider_user_id = "spotify_user_123"
        connection.access_token = "valid_token"
        connection.refresh_token = "refresh_token"
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)
        connection.credentials = None

        result = await service.get_valid_spotify_token(connection)

        assert result == "valid_token"
        # Redis lock should not be called for valid token
        mock_redis.set.assert_not_called()
        # DB commit should not be called
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_expired_token_refresh_success(self):
        """Test successful token refresh for expired token."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis.delete.return_value = 1  # Lock released

        service = IntegrationsService(db=mock_db, redis=mock_redis)

        # Create connection with expired token
        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.provider_name = "spotify"
        connection.provider_user_id = "spotify_user_123"
        connection.access_token = "old_token"
        connection.refresh_token = "refresh_token"
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        connection.credentials = None

        # Mock successful Spotify API response
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
        }

        with patch("backend.app.services.integrations_service.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = "test_client_id"
            mock_settings.SPOTIFY_CLIENT_SECRET = "test_client_secret"

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                mock_client_cls.return_value = mock_client

                result = await service.get_valid_spotify_token(connection)

        assert result == "new_token"
        assert connection.access_token == "new_token"
        assert connection.refresh_token == "new_refresh"
        # Lock should be acquired and released
        mock_redis.set.assert_called_once()
        mock_redis.delete.assert_called_once()
        # DB should be committed
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_refresh_no_refresh_token(self):
        """Test error when refresh token is missing."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        service = IntegrationsService(db=mock_db, redis=mock_redis)

        # Connection without refresh token
        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.access_token = "old_token"
        connection.refresh_token = None
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)

        with pytest.raises(TokenRefreshError) as exc_info:
            await service.get_valid_spotify_token(connection)

        assert "No refresh token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_refresh_spotify_api_error(self):
        """Test handling of Spotify API errors during refresh."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1

        service = IntegrationsService(db=mock_db, redis=mock_redis)

        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.access_token = "old_token"
        connection.refresh_token = "refresh_token"
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        connection.credentials = None

        # Mock failed Spotify API response
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant", "error_description": "Token revoked"}

        with patch("backend.app.services.integrations_service.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = "test_client_id"
            mock_settings.SPOTIFY_CLIENT_SECRET = "test_client_secret"

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                mock_client_cls.return_value = mock_client

                with pytest.raises(SpotifyAPIError) as exc_info:
                    await service.get_valid_spotify_token(connection)

        assert "Failed to refresh Spotify token" in str(exc_info.value)
        # Lock should still be released even on error
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh_uses_locking(self):
        """Test that token refresh uses distributed locking mechanism."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis.delete.return_value = 1  # Lock released

        service = IntegrationsService(db=mock_db, redis=mock_redis)

        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.access_token = "old_token"
        connection.refresh_token = "refresh_token"
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        connection.credentials = None

        # Mock successful Spotify response
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
        }

        with patch("backend.app.services.integrations_service.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = "test_client_id"
            mock_settings.SPOTIFY_CLIENT_SECRET = "test_client_secret"

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                mock_client_cls.return_value = mock_client

                result = await service.get_valid_spotify_token(connection)

        assert result == "new_token"
        # Verify lock was acquired and released
        mock_redis.set.assert_called_once()
        mock_redis.delete.assert_called_once()
        # Verify lock key includes connection ID (with "lock:" prefix from DistributedLock)
        lock_key_arg = mock_redis.set.call_args[0][0]
        assert f"lock:token_refresh:{connection.id}" == lock_key_arg

    @pytest.mark.asyncio
    async def test_token_refresh_missing_credentials(self):
        """Test error when Spotify credentials are missing."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_redis = AsyncMock()
        service = IntegrationsService(db=mock_db, redis=mock_redis)

        connection = MagicMock(spec=ServiceConnection)
        connection.id = uuid.uuid4()
        connection.user_id = uuid.uuid4()
        connection.access_token = "old_token"
        connection.refresh_token = "refresh_token"
        connection.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        connection.credentials = None

        with patch("backend.app.services.integrations_service.settings") as mock_settings:
            mock_settings.SPOTIFY_CLIENT_ID = None
            mock_settings.SPOTIFY_CLIENT_SECRET = None

            with pytest.raises(TokenRefreshError) as exc_info:
                await service.get_valid_spotify_token(connection)

        assert "credentials not found" in str(exc_info.value).lower()
