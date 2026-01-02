from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_async_session
from backend.app.models.service_connection import ServiceConnection
from backend.app.schemas.playlist import (
    GenerationRequest,
    VerificationRequest,
    VerificationResponse,
    TrackCreate,
    PlaylistCreate,
    BuildResponse,
)
from backend.app.services.ai_service import AIService
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User
from backend.core.client import SpotifyPlaylistBuilder

router = APIRouter()


def get_ai_service():
    return AIService()


@router.post("/generate", response_model=List[TrackCreate])
async def generate_playlist_endpoint(
    request: GenerationRequest,
    ai_service: AIService = Depends(get_ai_service),
    user: User = Depends(current_active_user),
):
    """
    Generate a playlist based on a prompt and optional artists.
    """
    try:
        tracks = ai_service.generate(
            prompt=request.prompt, count=request.count, artists=request.artists
        )
        return tracks
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
    playlist: PlaylistCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Build a playlist on a connected service (Spotify).
    """
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

    # 2. Use the token to build the playlist
    try:
        builder = SpotifyPlaylistBuilder(access_token=conn.access_token)
        # Convert Pydantic tracks to dicts for the core logic
        tracks_dict = [t.model_dump() for t in playlist.tracks]

        # Use core logic to create the playlist
        pid = builder.create_playlist(
            playlist.name, playlist.description or "", public=playlist.public
        )
        actual_tracks, failed = builder.add_tracks_to_playlist(pid, tracks_dict)

        # Calculate total duration from actual metadata
        total_ms = sum(t.get("duration_ms", 0) for t in actual_tracks)

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
