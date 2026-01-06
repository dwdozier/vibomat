# Track Plan: Playlist Lifecycle & Sync Engine

## Phase 1: Soft-Delete Implementation

- [~] Add `deleted_at` column to `Playlist` model and migration.
- [ ] Update `Playlist` CRUD operations to handle soft-deletes (filter out deleted by default).
- [ ] Implement `delete` endpoint to perform soft-delete.
- [ ] Implement `restore` endpoint to recover soft-deleted playlists.
- [ ] Create a Celery/background task to purge playlists older than 30 days.

## Phase 2: Playlist Import

- [ ] Create `PlaylistImport` schema.
- [ ] Implement service logic to fetch playlist details from Provider (Spotify).
- [ ] Implement logic to save imported playlist and tracks to DB.
- [ ] Create API endpoint for importing playlists.

## Phase 3: Sync Engine

- [ ] Design Sync Engine architecture (state tracking, diffing).
- [ ] Implement `sync_playlist` task.
- [ ] Add `last_synced_at` to `Playlist`.
- [ ] Implement periodic background task for sync.
- [ ] Add "Sync Now" button/endpoint for users.
