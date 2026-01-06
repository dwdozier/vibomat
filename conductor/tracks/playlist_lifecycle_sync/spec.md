# Track Specification: Playlist Lifecycle & Sync Engine

## Goal

Make playlists robust with recovery options and bi-directional synchronization.

## Key Features

- **Soft-Delete:** Implement "Soft-Delete" for playlists with a 30-day auto-purge policy.
- **Playlist Import:** Import existing playlists from services.
- **Sync Engine:** Build the bi-directional sync engine (Periodic + On-Demand).

## Detailed Requirements

### 1. Soft-Delete & Recovery

- Playlists should not be permanently deleted immediately.
- A `deleted_at` timestamp should be used.
- A background task should permanently remove playlists deleted more than 30 days ago.
- An endpoint to restore a soft-deleted playlist.

### 2. Playlist Import

- User can select an existing playlist from a connected provider (e.g., Spotify).
- The system imports the playlist metadata and tracks into the local database.

### 3. Bi-Directional Sync

- **On-Demand:** User can trigger a sync manually.
- **Periodic:** Background job to sync playlists periodically.
- **Conflict Resolution:** Strategy for handling changes on both ends (e.g., source of truth is
  the provider, or last write wins).
