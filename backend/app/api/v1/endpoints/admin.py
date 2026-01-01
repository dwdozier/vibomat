from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.db.session import get_async_session
from backend.app.core.auth.fastapi_users import current_active_superuser
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection
from backend.app.models.user import OAuthAccount
from backend.app.schemas.user import UserRead
from backend.app.schemas.playlist import PlaylistRead
from typing import List

router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    user: User = Depends(current_active_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get high-level system statistics for the admin dashboard.
    """
    user_count = await db.execute(select(func.count(User.id)))
    playlist_count = await db.execute(select(func.count(Playlist.id)))
    connection_count = await db.execute(select(func.count(ServiceConnection.id)))
    oauth_count = await db.execute(select(func.count(OAuthAccount.id)))

    return {
        "users": user_count.scalar(),
        "playlists": playlist_count.scalar(),
        "connections": connection_count.scalar(),
        "oauth_accounts": oauth_count.scalar(),
    }


@router.get("/users", response_model=List[UserRead])
async def list_users(
    user: User = Depends(current_active_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """List all users in the system."""
    result = await db.execute(select(User))
    return result.unique().scalars().all()


@router.get("/playlists", response_model=List[PlaylistRead])
async def list_playlists(
    user: User = Depends(current_active_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """List all playlists in the system."""
    result = await db.execute(select(Playlist))
    return result.scalars().all()


@router.get("/connections")
async def list_connections(
    user: User = Depends(current_active_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    """List all service connections in the system."""
    result = await db.execute(select(ServiceConnection))
    # We don't have a schema for ServiceConnectionRead yet, so we'll just return the dicts
    connections = result.scalars().all()
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "provider_name": c.provider_name,
            "expires_at": c.expires_at,
        }
        for c in connections
    ]
