import httpx
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.service_connection import ServiceConnection
from backend.app.core.config import settings


class IntegrationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_valid_spotify_token(self, connection: ServiceConnection) -> str:
        """
        Check if the current token is expired and refresh if necessary.
        """
        # DB stores naive UTC. Ensure we compare correctly.
        now_naive = datetime.now(UTC).replace(tzinfo=None)

        if connection.expires_at and connection.expires_at > now_naive + timedelta(minutes=5):
            return connection.access_token

        # Token is expired or expiring soon, refresh it
        if not connection.refresh_token:
            raise Exception("No refresh token available for Spotify relay.")

        client_id = settings.SPOTIFY_CLIENT_ID
        client_secret = settings.SPOTIFY_CLIENT_SECRET

        if connection.credentials:
            client_id = connection.credentials.get("client_id", client_id)
            client_secret = connection.credentials.get("client_secret", client_secret)

        if not client_id or not client_secret:
            raise Exception("Spotify Relay credentials not found.")

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
                error_data = response.json()
                raise Exception(
                    f"Failed to refresh Spotify token: "
                    f"{error_data.get('error_description', error_data.get('error'))}"
                )

            token_data = response.json()
            connection.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                connection.refresh_token = token_data["refresh_token"]

            connection.expires_at = (datetime.now(UTC) + timedelta(seconds=token_data["expires_in"])).replace(
                tzinfo=None
            )

            await self.db.commit()
            return connection.access_token
