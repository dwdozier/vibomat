from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from backend.app.schemas.playlist import (
    GenerationRequest,
    VerificationRequest,
    VerificationResponse,
    TrackCreate,
    PlaylistCreate,
)
from backend.app.services.ai_service import AIService

router = APIRouter()


def get_ai_service():
    return AIService()


@router.post("/generate", response_model=List[TrackCreate])
async def generate_playlist_endpoint(
    request: GenerationRequest, ai_service: AIService = Depends(get_ai_service)
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify", response_model=VerificationResponse)
async def verify_tracks_endpoint(
    request: VerificationRequest, ai_service: AIService = Depends(get_ai_service)
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


@router.post("/export")
async def export_playlist(playlist: PlaylistCreate):
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
