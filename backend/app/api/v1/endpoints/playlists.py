from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app.db.session import get_async_session
from backend.app.models.service_connection import ServiceConnection
from backend.app.schemas.playlist import (
    GenerationRequest,
    VerificationRequest,
    VerificationResponse,
    PlaylistCreate,
    BuildResponse,
    PlaylistGenerationResponse,
    PlaylistRead,
    PlaylistBuildRequest,
)
from backend.app.services.ai_service import AIService
from backend.app.services.integrations_service import IntegrationsService
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User
from backend.app.models.playlist import Playlist as PlaylistModel
from backend.core.client import SpotifyPlaylistBuilder
import uuid

router = APIRouter()


def get_ai_service():
    return AIService()


@router.post("/", response_model=PlaylistRead)
async def create_playlist(
    playlist: PlaylistCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new playlist in the database.
    """
    # Convert Pydantic models to dicts for JSON storage
    tracks_dict = [t.model_dump() for t in playlist.tracks]

    db_playlist = PlaylistModel(
        user_id=user.id,
        name=playlist.name,
        description=playlist.description,
        public=playlist.public,
        content_json={"tracks": tracks_dict},
        status="draft",
    )
    db.add(db_playlist)
    await db.commit()
    await db.refresh(db_playlist)
    return db_playlist


@router.get("/me", response_model=List[PlaylistRead])
async def get_my_playlists(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    List all playlists created by the current user.
    """
    result = await db.execute(
        select(PlaylistModel)
        .where(PlaylistModel.user_id == user.id)
        .order_by(PlaylistModel.id.desc())
    )
    return result.scalars().all()


@router.get("/{playlist_id}", response_model=PlaylistRead)
async def get_playlist(
    playlist_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific playlist by ID.
    """
    result = await db.execute(select(PlaylistModel).where(PlaylistModel.id == playlist_id))
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Check ownership or visibility (if public read logic is added later)
    if playlist.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this playlist")

    return playlist


@router.patch("/{playlist_id}", response_model=PlaylistRead)
async def update_playlist(
    playlist_id: uuid.UUID,
    playlist_update: PlaylistCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update a playlist (e.g. content, name).
    """
    result = await db.execute(select(PlaylistModel).where(PlaylistModel.id == playlist_id))
    db_playlist = result.scalar_one_or_none()

    if not db_playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if db_playlist.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this playlist")

    db_playlist.name = playlist_update.name
    db_playlist.description = playlist_update.description
    db_playlist.public = playlist_update.public

    # Update content
    tracks_dict = [t.model_dump() for t in playlist_update.tracks]
    db_playlist.content_json = {"tracks": tracks_dict}

    await db.commit()
    await db.refresh(db_playlist)
    return db_playlist


@router.post("/generate", response_model=PlaylistGenerationResponse)
async def generate_playlist_endpoint(
    request: GenerationRequest,
    ai_service: AIService = Depends(get_ai_service),
    user: User = Depends(current_active_user),
):
    """
    Generate a playlist based on a prompt and optional artists.
    """
    try:
        # ai_service.generate now returns {title, description, tracks}
        result = ai_service.generate(
            prompt=request.prompt, count=request.count, artists=request.artists
        )
        return result
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify", response_model=VerificationResponse)
async def verify_tracks_endpoint(
    request: VerificationRequest,
    ai_service: AIService = Depends(get_ai_service),
    user: User = Depends(current_active_user),
):
    """
    Verify a list of tracks against metadata sources (MusicBrainz/Discogs).
    """
    try:
        # Convert Pydantic models to dicts for the service
        tracks_dict = [t.model_dump() for t in request.tracks]
        verified, rejected = ai_service.verify_tracks(tracks_dict)
        return {"verified": verified, "rejected": rejected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build", response_model=BuildResponse)
async def build_playlist_endpoint(
    request: PlaylistBuildRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Build a playlist on a connected service (Spotify).
    """
    playlist_data = request.playlist_data
    db_playlist = None

    if request.playlist_id:
        result = await db.execute(
            select(PlaylistModel).where(PlaylistModel.id == request.playlist_id)
        )
        db_playlist = result.scalar_one_or_none()
        if db_playlist and db_playlist.user_id == user.id:
            # Use data from DB
            # We will use db_playlist content below directly
            pass

    if not playlist_data and not db_playlist:
        raise HTTPException(status_code=400, detail="No playlist data provided.")

    # 1. Fetch Spotify connection for the user
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id, ServiceConnection.provider_name == "spotify"
        )
    )
    conn = result.scalar_one_or_none()

    if not conn:
        raise HTTPException(
            status_code=400, detail="Spotify relay station not connected. Please go to Settings."
        )

    # 2. Ensure token is valid
    integrations_service = IntegrationsService(db)
    try:
        access_token = await integrations_service.get_valid_spotify_token(conn)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to refresh Spotify token: {str(e)}")

    # 3. Use the token to build the playlist
    try:
        builder = SpotifyPlaylistBuilder(access_token=access_token)

        # Determine inputs
        if db_playlist:
            tracks_dict = db_playlist.content_json.get("tracks", [])
            name = db_playlist.name
            description = db_playlist.description or ""
            public = db_playlist.public
        elif playlist_data:
            tracks_dict = [t.model_dump() for t in playlist_data.tracks]
            name = playlist_data.name
            description = playlist_data.description or ""
            public = playlist_data.public
        else:
            # Should be caught above
            raise HTTPException(status_code=400, detail="No playlist data.")

        # Use core logic to create the playlist
        pid = builder.create_playlist(name, description, public=public)
        actual_tracks, failed = builder.add_tracks_to_playlist(pid, tracks_dict)

        # Calculate total duration from actual metadata
        total_ms = sum(t.get("duration_ms", 0) for t in actual_tracks)

        # Update DB status if it exists
        if db_playlist:
            db_playlist.status = "transmitted"
            db_playlist.provider = "spotify"
            db_playlist.provider_id = pid
            db_playlist.total_duration_ms = total_ms
            await db.commit()

        return {
            "status": "success",
            "playlist_id": pid,
            "url": f"https://open.spotify.com/playlist/{pid}",
            "failed_tracks": failed,
            "actual_tracks": actual_tracks,
            "total_duration_ms": total_ms,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to build playlist: {str(e)}")


@router.post("/export")
async def export_playlist(
    playlist: PlaylistCreate,
    user: User = Depends(current_active_user),
):
    """
    Export a playlist schema to a downloadable JSON file.
    """
    content = playlist.model_dump_json(indent=2)
    filename = playlist.name.lower().replace(" ", "_")
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.json"},
    )
