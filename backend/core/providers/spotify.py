from typing import List, Optional
import spotipy
from .base import BaseMusicProvider
from backend.core.utils.helpers import _similarity, _determine_version
import logging

logger = logging.getLogger("backend.core.providers.spotify")


class SpotifyProvider(BaseMusicProvider):
    def __init__(self, auth_token: str):
        self.sp = spotipy.Spotify(auth=auth_token)
        self._user_id = None

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            user = self.sp.current_user()
            if user is None:
                raise Exception("Failed to authenticate with Spotify")
            self._user_id = user["id"]
        return self._user_id

    async def search_track(
        self,
        artist: str,
        track: str,
        album: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[dict]:
        # Implementation logic moved from client.py, adapted for async if needed
        # For now, keeping synchronous calls but wrapped in async interface

        if album:
            query = f"track:{track} artist:{artist} album:{album}"
            results = self.sp.search(q=query, type="track", limit=1)
            if results and results["tracks"]["items"]:
                item = results["tracks"]["items"][0]
                return {
                    "artist": ", ".join([a["name"] for a in item["artists"]]),
                    "track": item["name"],
                    "album": item["album"]["name"],
                    "uri": item["uri"],
                }

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
            return {
                "artist": ", ".join([a["name"] for a in best_match["artists"]]),
                "track": best_match["name"],
                "album": best_match["album"]["name"],
                "uri": best_match["uri"],
            }
        return None

    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        playlist = self.sp.user_playlist_create(user=self.user_id, name=name, public=public, description=description)
        return playlist["id"]

    async def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        # Spotify has a 100-track limit per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            self.sp.playlist_add_items(playlist_id, batch)

    async def replace_playlist_tracks(self, playlist_id: str, track_uris: List[str]) -> None:
        """Replace all tracks in a Spotify playlist with the given list of URIs."""
        # Spotify has a 100-track limit per request for this endpoint as well
        first_batch = track_uris[:100]
        remaining_uris = track_uris[100:]

        # First call uses replace_playlist_items
        self.sp.playlist_replace_items(playlist_id, first_batch)

        # Subsequent calls use playlist_add_items
        for i in range(0, len(remaining_uris), 100):
            batch = remaining_uris[i : i + 100]
            self.sp.playlist_add_items(playlist_id, batch)

    async def get_playlist(self, playlist_id: str) -> dict:
        results = self.sp.playlist(playlist_id)
        tracks = results["tracks"]["items"]

        # Helper to follow pagination
        current_page = results["tracks"]
        while current_page["next"]:
            current_page = self.sp.next(current_page)
            tracks.extend(current_page["items"])

        results["tracks"]["items"] = tracks
        return results
