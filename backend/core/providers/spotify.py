from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import spotipy
from .base import BaseMusicProvider
from backend.core.utils.helpers import _similarity, _determine_version
from backend.app.schemas.playlist import PlayabilityReason
import logging
import asyncio

logger = logging.getLogger("backend.core.providers.spotify")


class SpotifyProvider(BaseMusicProvider):
    def __init__(self, auth_token: str, market: Optional[str] = None):
        """
        Initialize Spotify provider.

        Args:
            auth_token: Spotify authentication token
            market: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB') for market-specific queries
        """
        self.sp = spotipy.Spotify(auth=auth_token)
        self._user_id = None
        self.market = market

    async def get_user_id(self) -> str:
        if self._user_id is None:
            user = await asyncio.to_thread(self.sp.current_user)
            if user is None:
                raise Exception("Failed to authenticate with Spotify")
            self._user_id = user["id"]
        return self._user_id

    async def get_user_market(self) -> Optional[str]:
        """
        Get the user's market (country) from their Spotify profile.

        Returns:
            ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'JP') or None if unavailable

        Raises:
            Exception: If authentication fails
        """
        try:
            user = await asyncio.to_thread(self.sp.current_user)
            if user is None:
                raise Exception("Failed to authenticate with Spotify")

            # Spotify returns 'country' field in user profile
            market = user.get("country")
            if market:
                logger.info(f"Detected user market: {market}")
            else:
                logger.warning("User market not available in Spotify profile")

            return market
        except Exception as e:
            logger.error(f"Failed to get user market: {e}")
            raise

    async def check_track_playability(self, track_uri: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a track is playable on Spotify.

        Args:
            track_uri: Spotify URI (spotify:track:xxx)
            market: ISO 3166-1 alpha-2 country code (e.g., 'US'). If None, uses instance market.

        Returns:
            Dictionary with playability information:
            {
                "playable": bool,
                "reason": PlayabilityReason value,
                "available_markets": List[str] or None,
                "is_local": bool,
                "restrictions": Dict[str, str] or None,
                "checked_at": ISO 8601 timestamp
            }
        """
        # Extract track ID from URI
        track_id = track_uri.split(":")[-1] if ":" in track_uri else track_uri

        # Use provided market or instance market
        effective_market = market or self.market

        # Query Spotify API for track details
        try:
            track_data = await asyncio.to_thread(self.sp.track, track_id, market=effective_market)
        except Exception as e:
            logger.warning(f"Failed to check playability for track {track_id}: {e}")
            return {
                "playable": False,
                "reason": PlayabilityReason.UNKNOWN,
                "available_markets": None,
                "is_local": False,
                "restrictions": None,
                "checked_at": datetime.now(UTC).isoformat(),
            }

        # Extract playability information
        is_playable = track_data.get("is_playable", True)  # Default True if not present
        available_markets = track_data.get("available_markets", [])
        restrictions = track_data.get("restrictions", {})
        is_local = track_data.get("is_local", False)

        # Determine reason for playability status
        if is_playable:
            reason = PlayabilityReason.PLAYABLE
        elif is_local:
            reason = PlayabilityReason.LOCAL_FILE_ONLY
        elif restrictions:
            restriction_reason = restrictions.get("reason", "")
            if restriction_reason == "market":
                reason = PlayabilityReason.REGION_RESTRICTED
            elif restriction_reason == "explicit":
                reason = PlayabilityReason.EXPLICIT_CONTENT_RESTRICTED
            else:
                reason = PlayabilityReason.UNAVAILABLE
        elif effective_market and effective_market not in available_markets:
            reason = PlayabilityReason.REGION_RESTRICTED
        else:
            reason = PlayabilityReason.UNAVAILABLE

        return {
            "playable": is_playable,
            "reason": reason,
            "available_markets": available_markets if not is_playable and available_markets else None,
            "is_local": is_local,
            "restrictions": restrictions if restrictions else None,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    async def search_track(
        self,
        artist: str,
        track: str,
        album: Optional[str] = None,
        version: Optional[str] = None,
        check_playability: bool = False,
    ) -> Optional[dict]:
        # Implementation logic moved from client.py, adapted for async if needed
        # For now, keeping synchronous calls but wrapped in async interface

        if album:
            query = f"track:{track} artist:{artist} album:{album}"
            results = await asyncio.to_thread(self.sp.search, q=query, type="track", limit=1)
            if results and results["tracks"]["items"]:
                item = results["tracks"]["items"][0]
                result = {
                    "artist": ", ".join([a["name"] for a in item["artists"]]),
                    "track": item["name"],
                    "album": item["album"]["name"],
                    "uri": item["uri"],
                }

                # Check playability if requested
                if check_playability:
                    playability_info = await self.check_track_playability(item["uri"])
                    result["playability"] = playability_info

                return result

        query = f"track:{track} artist:{artist}"
        results = await asyncio.to_thread(self.sp.search, q=query, type="track", limit=20)
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
            result = {
                "artist": ", ".join([a["name"] for a in best_match["artists"]]),
                "track": best_match["name"],
                "album": best_match["album"]["name"],
                "uri": best_match["uri"],
            }

            # Check playability if requested
            if check_playability:
                playability_info = await self.check_track_playability(best_match["uri"])
                result["playability"] = playability_info

            return result
        return None

    async def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        user_id = await self.get_user_id()
        playlist = await asyncio.to_thread(
            self.sp.user_playlist_create, user=user_id, name=name, public=public, description=description
        )
        return playlist["id"]

    async def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        # Spotify has a 100-track limit per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            await asyncio.to_thread(self.sp.playlist_add_items, playlist_id, batch)

    async def replace_playlist_tracks(self, playlist_id: str, track_uris: List[str]) -> None:
        """Replace all tracks in a Spotify playlist with the given list of URIs."""
        # Spotify has a 100-track limit per request for this endpoint as well
        first_batch = track_uris[:100]
        remaining_uris = track_uris[100:]

        # First call uses replace_playlist_items
        await asyncio.to_thread(self.sp.playlist_replace_items, playlist_id, first_batch)

        # Subsequent calls use playlist_add_items
        for i in range(0, len(remaining_uris), 100):
            batch = remaining_uris[i : i + 100]
            await asyncio.to_thread(self.sp.playlist_add_items, playlist_id, batch)

    async def get_playlist(self, playlist_id: str) -> dict:
        results = await asyncio.to_thread(self.sp.playlist, playlist_id)
        tracks = results["tracks"]["items"]

        # Helper to follow pagination
        current_page = results["tracks"]
        while current_page["next"]:
            current_page = await asyncio.to_thread(self.sp.next, current_page)
            tracks.extend(current_page["items"])

        results["tracks"]["items"] = tracks
        return results
