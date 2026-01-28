import httpx
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.distributed_lock import DistributedLock
from backend.app.exceptions import TokenRefreshError, SpotifyAPIError
from backend.app.models.service_connection import ServiceConnection

logger = logging.getLogger(__name__)


class IntegrationsService:
    def __init__(self, db: AsyncSession, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis

    async def get_valid_spotify_token(self, connection: ServiceConnection) -> str:
        """
        Check if the current token is expired and refresh if necessary.

        Uses distributed locking to prevent race conditions when multiple processes
        attempt to refresh the same token concurrently.

        Args:
            connection: ServiceConnection with Spotify credentials

        Returns:
            Valid access token

        Raises:
            TokenRefreshError: If token refresh fails
            SpotifyAPIError: If Spotify API returns an error
        """
        # DB stores naive UTC. Ensure we compare correctly.
        now_naive = datetime.now(UTC).replace(tzinfo=None)

        # If token is still valid (with 5 minute buffer), return it
        if connection.expires_at and connection.expires_at > now_naive + timedelta(minutes=5):
            logger.debug(f"Using cached valid token for connection {connection.id}")
            # Lazy-load market if missing
            await self._ensure_market_populated(connection)
            return connection.access_token

        # Token is expired or expiring soon, refresh it
        logger.info(f"Token refresh required for connection {connection.id}")

        if not connection.refresh_token:
            raise TokenRefreshError(
                "No refresh token available for Spotify relay",
                details={"connection_id": connection.id},
            )

        # Get credentials
        client_id = settings.SPOTIFY_CLIENT_ID
        client_secret = settings.SPOTIFY_CLIENT_SECRET

        if connection.credentials:
            client_id = connection.credentials.get("client_id", client_id)
            client_secret = connection.credentials.get("client_secret", client_secret)

        if not client_id or not client_secret:
            raise TokenRefreshError(
                "Spotify Relay credentials not found",
                details={"connection_id": connection.id},
            )

        # Use distributed lock to prevent concurrent refresh attempts
        lock_key = f"token_refresh:{connection.id}"

        if self.redis:
            # Use lock with 30-second timeout, block for up to 10 seconds
            async with DistributedLock(
                self.redis, lock_key, timeout=30, blocking=True, max_wait=10.0, retry_interval=0.1
            ):
                token = await self._refresh_spotify_token(connection, client_id, client_secret)
        else:
            # No Redis available, proceed without locking (not recommended for production)
            logger.warning(
                f"No Redis client available for connection {connection.id}, " "proceeding without distributed lock"
            )
            token = await self._refresh_spotify_token(connection, client_id, client_secret)

        # Lazy-load market if missing after token refresh
        await self._ensure_market_populated(connection)
        return token

    async def _refresh_spotify_token(self, connection: ServiceConnection, client_id: str, client_secret: str) -> str:
        """
        Perform the actual token refresh with Spotify API.

        This is separated from get_valid_spotify_token to allow the lock to be
        held only during the refresh operation.

        Args:
            connection: ServiceConnection to refresh
            client_id: Spotify client ID
            client_secret: Spotify client secret

        Returns:
            New access token

        Raises:
            SpotifyAPIError: If Spotify API returns an error
        """
        logger.info(
            f"Refreshing Spotify token for connection {connection.id}",
            extra={
                "connection_id": connection.id,
                "user_id": connection.user_id,
            },
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": connection.refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                )

                if response.status_code != 200:
                    # Parse error response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error_description", error_data.get("error", "Unknown error"))
                    except Exception:
                        error_msg = f"HTTP {response.status_code}"

                    logger.error(
                        f"Spotify token refresh failed for connection {connection.id}: {error_msg}",
                        extra={
                            "connection_id": connection.id,
                            "status_code": response.status_code,
                            "error": error_msg,
                        },
                    )

                    raise SpotifyAPIError(
                        f"Failed to refresh Spotify token: {error_msg}",
                        status_code=502,
                        details={
                            "connection_id": connection.id,
                            "spotify_status_code": response.status_code,
                            "error": error_msg,
                        },
                    )

                # Parse successful response
                token_data = response.json()
                connection.access_token = token_data["access_token"]

                if "refresh_token" in token_data:
                    connection.refresh_token = token_data["refresh_token"]

                connection.expires_at = (datetime.now(UTC) + timedelta(seconds=token_data["expires_in"])).replace(
                    tzinfo=None
                )

                await self.db.commit()

                logger.info(
                    f"Successfully refreshed Spotify token for connection {connection.id}",
                    extra={
                        "connection_id": connection.id,
                        "expires_at": connection.expires_at.isoformat(),
                    },
                )

                return connection.access_token

        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error during token refresh for connection {connection.id}: {e}",
                extra={"connection_id": connection.id},
                exc_info=True,
            )
            raise SpotifyAPIError(
                f"HTTP error during token refresh: {str(e)}",
                status_code=502,
                details={"connection_id": connection.id, "error": str(e)},
            ) from e

    async def _ensure_market_populated(self, connection: ServiceConnection) -> None:
        """
        Lazy-load market from Spotify if not already populated.

        This handles cases where:
        - Market was not set during OAuth flow
        - Backfill migration failed due to expired tokens
        - Legacy connections created before market feature

        Args:
            connection: ServiceConnection to check/update
        """
        # Skip if market already populated or not a Spotify connection
        if connection.market or connection.provider_name != "spotify":
            return

        try:
            from backend.core.providers.spotify import SpotifyProvider

            logger.info(f"Lazy-loading market for connection {connection.id}")
            provider = SpotifyProvider(auth_token=connection.access_token, market=None)
            market = await provider.get_user_market()

            if market:
                connection.market = market
                await self.db.commit()
                logger.info(
                    f"Market '{market}' populated for connection {connection.id}",
                    extra={"connection_id": connection.id, "market": market},
                )
            else:
                logger.warning(
                    f"No market available for connection {connection.id}",
                    extra={"connection_id": connection.id},
                )

        except Exception as e:
            # Log but don't fail the main operation
            logger.warning(
                f"Failed to lazy-load market for connection {connection.id}: {e}",
                extra={"connection_id": connection.id},
            )
