from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from backend.app.db.session import get_async_session
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User
from backend.app.models.service_connection import ServiceConnection
import os
import uuid

router = APIRouter()

# System defaults
DEFAULT_SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
DEFAULT_SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv(
    "SPOTIFY_REDIRECT_URI",
    "http://localhost/api/v1/integrations/spotify/callback",
)


class RelayConfig(BaseModel):
    provider: str
    client_id: str
    client_secret: str


@router.post("/relay/config")
async def save_relay_config(
    config: RelayConfig,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Save user-specific relay credentials (Client ID/Secret).
    """
    # 1. Fetch existing connection or create a placeholder
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id,
            ServiceConnection.provider_name == config.provider,
        )
    )
    conn = result.scalar_one_or_none()

    if not conn:
        # Create a placeholder connection to store credentials even before OAuth
        conn = ServiceConnection(
            user_id=user.id,
            provider_name=config.provider,
            provider_user_id="PENDING",
            access_token="PENDING",
            credentials={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
            },
        )
        db.add(conn)
    else:
        conn.credentials = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }

    await db.commit()
    return {"status": "success", "message": "Relay credentials stored."}


@router.get("/spotify/login")
async def spotify_login(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Redirect the user to Spotify for authentication.
    """
    import urllib.parse

    # 1. Look for user-specific credentials
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id, ServiceConnection.provider_name == "spotify"
        )
    )
    conn = result.scalar_one_or_none()

    client_id = DEFAULT_SPOTIFY_CLIENT_ID
    if conn and conn.credentials:
        client_id = conn.credentials.get("client_id", client_id)

    if not client_id:
        raise HTTPException(
            status_code=400, detail="Spotify Client ID not configured for this relay."
        )

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": "playlist-modify-public playlist-modify-private",
        "state": str(user.id),
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return {"url": url}


@router.get("/spotify/callback")
async def spotify_callback(code: str, state: str, db: AsyncSession = Depends(get_async_session)):
    """
    Handle the callback from Spotify and store tokens.
    """
    import httpx
    from datetime import datetime, timedelta, UTC

    try:
        user_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter (User ID)")

    # 1. Fetch credentials for this user
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user_id, ServiceConnection.provider_name == "spotify"
        )
    )
    conn = result.scalar_one_or_none()

    client_id = DEFAULT_SPOTIFY_CLIENT_ID
    client_secret = DEFAULT_SPOTIFY_CLIENT_SECRET

    if conn and conn.credentials:
        client_id = conn.credentials.get("client_id", client_id)
        client_secret = conn.credentials.get("client_secret", client_secret)

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Spotify Relay credentials not found.")

    # 2. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        if response.status_code != 200:
            error_data = response.json()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Failed to get tokens from Spotify: "
                    f"{error_data.get('error_description', error_data.get('error'))}"
                ),
            )

        token_data = response.json()

        # 3. Get user info from Spotify
        user_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        spotify_user = user_response.json()

        # 4. Update or Create Connection
        expires_at = datetime.now(UTC) + timedelta(seconds=token_data["expires_in"])

        if not conn:
            conn = ServiceConnection(
                user_id=user_id,
                provider_name="spotify",
                provider_user_id=spotify_user["id"],
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at,
            )
            db.add(conn)
        else:
            conn.provider_user_id = spotify_user["id"]
            conn.access_token = token_data["access_token"]
            conn.refresh_token = token_data.get("refresh_token")
            conn.expires_at = expires_at

        await db.commit()

        return {"status": "success", "message": "Spotify relay connected!"}
