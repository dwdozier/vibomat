from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.db.session import get_async_session
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User, user_favorite_playlists
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection
from backend.app.schemas.user import UserPublic
from backend.app.schemas.playlist import PlaylistRead
from backend.app.services.metadata_service import MetadataService
from backend.core.providers.spotify import SpotifyProvider
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import httpx

router = APIRouter()


def get_http_client() -> httpx.AsyncClient:
    # NOTE: This should be managed by FastAPI lifespan events for a real app,
    # but for local development and testing, we use a simple instantiation.
    # We rely on the app's lifespan to create a client that the DI system can use.
    # Since we don't have a global DI for the client yet, we instantiate it here.
    return httpx.AsyncClient()


async def get_spotify_provider(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> SpotifyProvider:
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id,
            ServiceConnection.provider_name == "spotify",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection or not connection.access_token:
        raise HTTPException(status_code=404, detail="Spotify connection not found or invalid.")
    return SpotifyProvider(auth_token=connection.access_token)


def get_metadata_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    spotify_provider: SpotifyProvider = Depends(get_spotify_provider),
):
    return MetadataService(http_client=http_client, spotify_provider=spotify_provider)


class UserPreferencesUpdate(BaseModel):
    discogs_pat: Optional[str] = Field(None, description="Discogs Personal Access Token")


class ArtistEnrichRequest(BaseModel):
    artist_name: str


class AlbumEnrichRequest(BaseModel):
    artist_name: str
    album_name: str


@router.patch("/me/preferences")
async def update_preferences(
    update: UserPreferencesUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update the current user's preferences (e.g., Discogs PAT).
    """
    # Note: User model needs a field for preferences or discogs_pat
    # For now, we'll just mock the update as we need a migration to add the field
    return {"status": "success", "message": "Preferences updated (Mocked)"}


@router.post("/me/enrich/artist")
async def enrich_artist(
    request: ArtistEnrichRequest,
    metadata_service: MetadataService = Depends(get_metadata_service),
    user: User = Depends(current_active_user),
):
    """
    Fetch enriched metadata for an artist.
    """
    info = await metadata_service.get_artist_info(request.artist_name)
    if not info:
        raise HTTPException(status_code=404, detail="Artist metadata not found")
    return info


@router.post("/me/enrich/album")
async def enrich_album(
    request: AlbumEnrichRequest,
    metadata_service: MetadataService = Depends(get_metadata_service),
    user: User = Depends(current_active_user),
):
    """
    Fetch enriched metadata for an album.
    """
    info = await metadata_service.get_album_info(request.artist_name, request.album_name)
    if not info:
        raise HTTPException(status_code=404, detail="Album metadata not found")
    return info


@router.get("/by-handle/{handle}", response_model=UserPublic)
async def get_public_profile_by_handle(
    handle: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a user's public profile by their handle.
    """
    result = await db.execute(select(User).where(User.handle == handle))
    user = result.unique().scalar_one_or_none()
    if not user or not user.is_public:
        raise HTTPException(status_code=404, detail="User not found or profile is private")
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def get_public_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a user's public profile.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.unique().scalar_one_or_none()
    if not user or not user.is_public:
        raise HTTPException(status_code=404, detail="User not found or profile is private")
    return user


@router.get("/{user_id}/playlists", response_model=List[PlaylistRead])
async def get_public_playlists(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a user's public playlists.
    """
    # Verify user exists and is public
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.unique().scalar_one_or_none()
    if not user or not user.is_public:
        raise HTTPException(status_code=404, detail="User not found or profile is private")

    result = await db.execute(
        select(Playlist).where(Playlist.user_id == user_id, Playlist.public, Playlist.deleted_at.is_(None))
    )
    return result.scalars().all()


@router.get("/{user_id}/favorites", response_model=List[PlaylistRead])
async def get_favorited_playlists(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a user's favorited playlists from others.
    """
    # Verify user exists and is public
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.unique().scalar_one_or_none()
    if not user or not user.is_public:
        raise HTTPException(status_code=404, detail="User not found or profile is private")

    result = await db.execute(
        select(Playlist)
        .join(
            user_favorite_playlists,
            Playlist.id == user_favorite_playlists.c.playlist_id,
        )
        .where(user_favorite_playlists.c.user_id == user_id, Playlist.deleted_at.is_(None))
    )
    return result.scalars().all()


@router.post("/playlists/{playlist_id}/favorite")
async def favorite_playlist(
    playlist_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Favorite a playlist.
    """
    # Check if playlist exists and is public
    playlist_result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.deleted_at.is_(None))
    )
    playlist = playlist_result.scalar_one_or_none()
    if not playlist or not playlist.public:
        raise HTTPException(status_code=404, detail="Playlist not found or private")

    # Check if already favorited
    fav_result = await db.execute(
        select(user_favorite_playlists).where(
            user_favorite_playlists.c.user_id == user.id,
            user_favorite_playlists.c.playlist_id == playlist_id,
        )
    )
    if fav_result.scalar_one_or_none():
        return {"status": "success", "message": "Already favorited"}

    await db.execute(user_favorite_playlists.insert().values(user_id=user.id, playlist_id=playlist_id))
    await db.commit()
    return {"status": "success", "message": "Playlist favorited"}


@router.delete("/playlists/{playlist_id}/favorite")
async def unfavorite_playlist(
    playlist_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Unfavorite a playlist.
    """
    await db.execute(
        delete(user_favorite_playlists).where(
            user_favorite_playlists.c.user_id == user.id,
            user_favorite_playlists.c.playlist_id == playlist_id,
        )
    )
    await db.commit()
    return {"status": "success", "message": "Playlist unfavorited"}
