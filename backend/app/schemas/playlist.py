import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator


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


# Validation schemas for content_json field


class TrackContentSchema(BaseModel):
    """
    Validation schema for track content in playlist content_json field.

    Enforces strict validation to prevent malformed data:
    - artist and track: required, 1-255 characters
    - duration_ms: 0 to 86400000 (max 24 hours)
    - provider: must be one of known providers (spotify, discogs, musicbrainz)
    """

    artist: str = Field(..., min_length=1, max_length=255)
    track: str = Field(..., min_length=1, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    duration_ms: Optional[int] = Field(None, ge=0, le=86400000)
    provider: Optional[str] = Field(None)
    provider_id: Optional[str] = Field(None, max_length=255)
    uri: Optional[str] = Field(None, max_length=500)
    discogs_uri: Optional[str] = Field(None, max_length=500)

    @field_validator("artist", "track")
    @classmethod
    def strip_whitespace_and_validate(cls, v: str) -> str:
        """Strip whitespace and reject whitespace-only strings."""
        if v is None:
            raise ValueError("Field cannot be None")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace-only")
        return stripped

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, v: Optional[str]) -> Optional[str]:
        """Normalize provider to lowercase and validate against known providers."""
        if v is None:
            return None
        normalized = v.lower()
        valid_providers = {"spotify", "discogs", "musicbrainz"}
        if normalized not in valid_providers:
            raise ValueError(f"Invalid provider: {v}. Must be one of: {', '.join(valid_providers)}")
        return normalized


class PlaylistContentSchema(BaseModel):
    """
    Validation schema for playlist content_json field.

    Enforces:
    - name: required, non-empty
    - tracks: list of TrackContentSchema, max 10,000 tracks
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tracks: List[TrackContentSchema] = Field(..., max_length=10000)

    @field_validator("name")
    @classmethod
    def strip_name_whitespace(cls, v: str) -> str:
        """Strip whitespace from name."""
        if v is None:
            raise ValueError("Name cannot be None")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or whitespace-only")
        return stripped
