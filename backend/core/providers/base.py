from abc import ABC, abstractmethod
from typing import List, Optional


class BaseMusicProvider(ABC):
    """Abstract base class for music streaming providers."""

    @abstractmethod
    async def search_track(
        self,
        artist: str,
        track: str,
        album: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[dict]:
        """Search for a track and return its metadata."""
        pass

    @abstractmethod
    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        """Create a new playlist and return its provider-specific ID."""
        pass

    @abstractmethod
    async def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        """Add track URIs to a specific playlist."""
        pass

    @abstractmethod
    async def get_playlist(self, playlist_id: str) -> dict:
        """Fetch playlist details including tracks."""
        pass
