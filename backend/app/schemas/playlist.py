from typing import List, Optional
from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    artist: str
    track: str
    album: Optional[str] = None
    version: Optional[str] = Field(
        None, pattern="^(live|studio|compilation|remix|original|remaster)$"
    )


class TrackCreate(TrackBase):
    pass


class Track(TrackBase):
    uri: Optional[str] = None


class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None
    public: bool = False


class PlaylistCreate(PlaylistBase):
    tracks: List[TrackCreate]


class Playlist(PlaylistBase):
    tracks: List[Track]


class GenerationRequest(BaseModel):
    prompt: str
    count: int = 20
    artists: Optional[str] = None


class VerificationRequest(BaseModel):
    tracks: List[TrackCreate]


class VerificationResponse(BaseModel):
    verified: List[TrackCreate]
    rejected: List[str]
