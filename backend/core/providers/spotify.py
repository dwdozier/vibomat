from typing import List, Optional
import spotipy
from .base import BaseMusicProvider
from backend.core.utils.helpers import _similarity, _determine_version
from backend.core.metadata import MetadataVerifier
import logging

logger = logging.getLogger("backend.core.providers.spotify")


class SpotifyProvider(BaseMusicProvider):
    def __init__(self, auth_token: str):
        self.sp = spotipy.Spotify(auth=auth_token)
        self.metadata_verifier = MetadataVerifier()
        self.user_id = self.sp.current_user()["id"]

    async def search_track(
        self, artist: str, track: str, album: Optional[str] = None, version: Optional[str] = None
    ) -> Optional[str]:
        # Implementation logic moved from client.py, adapted for async if needed
        # For now, keeping synchronous calls but wrapped in async interface

        if album:
            query = f"track:{track} artist:{artist} album:{album}"
            results = self.sp.search(q=query, type="track", limit=1)
            if results and results["tracks"]["items"]:
                return results["tracks"]["items"][0]["uri"]

        query = f"track:{track} artist:{artist}"
        results = self.sp.search(q=query, type="track", limit=20)
        if results is None or not results["tracks"]["items"]:
            return None

        candidates = results["tracks"]["items"]
        best_match = None
        best_score = -1.0

        for item in candidates:
            score = 0.0
            item_name = item["name"]
            item_artists = [a["name"] for a in item["artists"]]
            item_album = item["album"]["name"]

            # Artist Match
            artist_match = max(_similarity(artist, a) for a in item_artists)
            score += artist_match * 30

            # Track Name Match
            track_match = _similarity(track, item_name)
            score += track_match * 40

            # Version Preference
            detected_version = _determine_version(item_name, item_album)
            if version == detected_version:
                score += 30
            elif not version and detected_version == "studio":
                score += 30

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score > 60:
            return best_match["uri"]
        return None

    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        playlist = self.sp.user_playlist_create(
            user=self.user_id, name=name, public=public, description=description
        )
        return playlist["id"]

    async def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        # Spotify has a 100-track limit per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            self.sp.playlist_add_items(playlist_id, batch)
