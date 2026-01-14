import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class TrackBase(BaseModel):
    artist: str
    track: str
    album: Optional[str] = None
    version: Optional[str] = Field(None, pattern="^[a-zA-Z0-9| ]*$")
    duration_ms: Optional[int] = None
    uri: Optional[str] = None
    discogs_uri: Optional[str] = None
    degraded_signal: Optional[bool] = None


class TrackCreate(TrackBase):
    pass


class BuildResponse(BaseModel):
    status: str
    playlist_id: str
    url: str
    failed_tracks: List[str]
    actual_tracks: List[TrackCreate]
    total_duration_ms: int


class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None
    public: bool = False


class PlaylistCreate(PlaylistBase):
    tracks: List[TrackCreate]


class Playlist(PlaylistBase):
    id: uuid.UUID
    user_id: uuid.UUID
    content_json: Dict[str, Any]
    total_duration_ms: Optional[int] = None
    status: str = "draft"
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    deleted_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlaylistRead(Playlist):
    pass


class PlaylistBuildRequest(BaseModel):
    playlist_id: Optional[uuid.UUID] = None
    # Optional override or fallback if ID not provided
    playlist_data: Optional[PlaylistCreate] = None


class GenerationRequest(BaseModel):
    prompt: str
    count: int = 20
    artists: Optional[str] = None


class PlaylistGenerationResponse(BaseModel):
    title: str
    description: Optional[str] = None
    tracks: List[TrackCreate]


class VerificationRequest(BaseModel):
    tracks: List[TrackCreate]


class VerificationResponse(BaseModel):
    verified: List[TrackCreate]
    rejected: List[str]


class PlaylistImport(BaseModel):
    provider: str = Field(..., description="Provider name (e.g. 'spotify')")
    provider_playlist_id: str
    import_tracks: bool = True
