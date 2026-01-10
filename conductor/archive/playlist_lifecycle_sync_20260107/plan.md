# Track Plan: Playlist Lifecycle & Sync Engine

## Phase 1: Soft-Delete Implementation

- [x] Add `deleted_at` column to `Playlist` model and migration. 10d1c13
- [x] Update `Playlist` CRUD operations to handle soft-deletes (filter out deleted
  by default). (Found to be complete)
- [x] Implement `delete` endpoint to perform soft-delete. (Found to be complete)
- [x] Implement `restore` endpoint to recover soft-deleted playlists. (Found to be complete)
- [x] Create a Celery/background task to purge playlists older than 30 days. (Found to be complete)

## Phase 2: Playlist Import

- [x] Create `PlaylistImport` schema. (Found to be complete)
- [x] Implement service logic to fetch playlist details from Provider (Spotify). (Found to be complete)
- [x] Implement logic to save imported playlist and tracks to DB. (Found to be complete)
- [x] Create API endpoint for importing playlists. (Found to be complete)

## Phase 3: Sync Engine

- [x] Design Sync Engine architecture (state tracking, diffing). (Completed with last_synced_at)
- [x] Implement `sync_playlist` task. (Completed in tasks.py)
- [x] Add `last_synced_at` to `Playlist`. (Completed with model/schema/migration)
- [x] Implement periodic background task for sync. (Completed in tasks.py)
- [x] Add "Sync Now" button/endpoint for users. (Completed in playlists.py)
