from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_async_session
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User
from backend.app.models.service_connection import ServiceConnection
import os
import uuid

router = APIRouter()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv(
    "SPOTIFY_REDIRECT_URI",
    "http://localhost/api/v1/integrations/spotify/callback",
)


@router.get("/spotify/login")
async def spotify_login(user: User = Depends(current_active_user)):
    """
    Redirect the user to Spotify for authentication.
    """
    import urllib.parse

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": "playlist-modify-public playlist-modify-private",
        "state": str(user.id),  # Simple CSRF/User association for now
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

    # 1. Validate state (User ID) immediately
    try:
        user_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter (User ID)")

    # 2. Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
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

        # 2. Get user info from Spotify
        user_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        spotify_user = user_response.json()

        # 3. Store in DB
        # Note: In a real app, we'd verify 'state' matches the user session
        expires_at = datetime.now(UTC) + timedelta(seconds=token_data["expires_in"])

        conn = ServiceConnection(
            user_id=user_id,
            provider_name="spotify",
            provider_user_id=spotify_user["id"],
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
        )

        db.add(conn)
        await db.commit()

        return {"status": "success", "message": "Spotify connected!"}
