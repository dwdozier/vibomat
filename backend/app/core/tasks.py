from datetime import datetime, timedelta, timezone
from typing import cast
import traceback
from uuid import UUID

from sqlalchemy import delete, select, CursorResult
from taskiq_redis import ListQueueBroker

from backend.app.core.config import settings
from backend.app.db.session import async_session_maker
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection
from backend.app.models.user import User
from backend.app.services.integrations_service import IntegrationsService
from backend.core.providers.spotify import SpotifyProvider

broker = ListQueueBroker(str(settings.REDIS_URL))


@broker.task
async def create_playlist_task(
    playlist_name: str,
    track_uris: list[str],
    auth_token: str,
) -> str:
    """Background task to create a playlist on Spotify."""
    provider = SpotifyProvider(auth_token=auth_token)
    playlist_id = await provider.create_playlist(playlist_name)
    await provider.add_tracks_to_playlist(playlist_id, track_uris)

    return playlist_id


@broker.task
async def sync_playlist_task(playlist_id: UUID) -> str:
    """
    Synchronizes a local playlist with its remote service provider.
    Currently implements a one-way sync from local DB to Spotify.
    """
    async with async_session_maker() as session:
        try:
            # 1. Fetch Playlist, User, and Connection
            stmt = (
                select(Playlist, User, ServiceConnection)
                .join(User)
                .join(
                    ServiceConnection,
                    (ServiceConnection.user_id == Playlist.user_id)
                    & (ServiceConnection.provider_name == Playlist.provider),
                    isouter=True,
                )
                .where(Playlist.id == playlist_id)
            )
            result = await session.execute(stmt)
            playlist, user, conn = result.first() or (None, None, None)

            if not playlist or not user:
                return f"Sync failed: Playlist {playlist_id} not found."

            if not playlist.provider or not playlist.provider_id:
                return f"Sync skipped: Playlist {playlist_id} is not linked to a remote provider."

            if playlist.provider != "spotify":
                return f"Sync skipped: Provider {playlist.provider} not supported for sync."

            if not conn:
                return f"Sync failed: User {user.id} has no active {playlist.provider} connection."

            # 2. Get valid token
            integrations_service = IntegrationsService(session)
            access_token = await integrations_service.get_valid_spotify_token(conn)

            # 3. Initialize Provider
            provider = SpotifyProvider(auth_token=access_token)

            # 4. Get track URIs from local content
            local_tracks = playlist.content_json.get("tracks", [])
            local_uris = [t["uri"] for t in local_tracks if t.get("uri") and t.get("provider") == "spotify"]

            # 5. Get remote track URIs (Assuming SpotifyProvider has a method for this)
            # For simplicity, we will force a full overwrite for the first pass of the sync engine.
            # A true diffing engine is more complex and will be addressed later if needed.
            # The builder logic provides a mechanism to replace all tracks.

            # We use the raw client to replace all tracks.
            await provider.replace_playlist_tracks(playlist.provider_id, local_uris)

            # 6. Update last_synced_at
            playlist.last_synced_at = datetime.now(timezone.utc)
            await session.commit()

            return f"Sync successful for playlist {playlist_id} on {playlist.provider}"

        except Exception as e:
            await session.rollback()
            # Log the error
            print(f"Error during sync_playlist_task for {playlist_id}: {e}")
            traceback.print_exc()
            return f"Sync failed for playlist {playlist_id}: {str(e)}"


@broker.task(schedule=timedelta(hours=6))  # Run every 6 hours
async def periodic_sync_dispatch_task() -> str:
    """
    Finds all playlists due for synchronization and dispatches sync tasks.
    A playlist is due if it has a provider_id and hasn't been synced in the last 24 hours.
    """
    SYNC_INTERVAL = timedelta(hours=24)
    cutoff = datetime.now(timezone.utc) - SYNC_INTERVAL

    async with async_session_maker() as session:
        # Find playlists that:
        # 1. Are linked to a provider (e.g., Spotify)
        # 2. Are not soft-deleted
        # 3. Have never been synced (last_synced_at is NULL) OR have not been synced
        #    in the last 24 hours
        stmt = select(Playlist.id).where(
            Playlist.provider.is_not(None),
            Playlist.provider_id.is_not(None),
            Playlist.deleted_at.is_(None),
            (Playlist.last_synced_at.is_(None)) | (Playlist.last_synced_at <= cutoff),
        )
        result = await session.execute(stmt)
        playlist_ids = result.scalars().all()

        if not playlist_ids:
            return "No playlists due for synchronization."

        # Dispatch sync tasks
        for p_id in playlist_ids:
            await sync_playlist_task.kiq(p_id)  # type: ignore[no-matching-overload]

        return f"Dispatched {len(playlist_ids)} sync tasks."


@broker.task
async def purge_deleted_playlists_task() -> str:
    """
    Purge playlists soft-deleted more than 30 days ago.
    """
    async with async_session_maker() as session:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        stmt = delete(Playlist).where(Playlist.deleted_at <= cutoff)
        result = await session.execute(stmt)
        await session.commit()
        return f"Purged {cast(CursorResult, result).rowcount} playlists"
