# Plan: Advanced Metadata & Matching Intelligence

## Phase 1: Discogs Integration and Core Metadata Fixes

- [x] Implement a `DiscogsClient` for fetching album/artist/track metadata. [72a8af7]
- [x] Update `backend/core/metadata.py` to use a multi-source lookup (Spotify -> [154730e]
  Discogs/MusicBrainz) to reduce missing data.
- [x] Enhance `MetadataVerifier` to flag tracks missing core data as "degraded signal." [2f105c3]
- [x] Update track schema to include fields for Discogs URI and degradation flag. [9511ded]
- [ ] Unit Test (Red/Green/Refactor): Verify multi-source lookup logic.

## Phase 2: Frontend Display of Degraded Signals

- [ ] Fetch and display additional metadata (e.g., Discogs album/artist) in the track modal.
- [ ] Implement UI component to display the "Degraded Signals" warning when core data is missing.
- [ ] Add basic styling for the warning indicator (e.g., a small red icon next to the track name).
- [ ] E2E Test (Red/Green/Refactor): Verify the degraded signal indicator appears correctly.

## Phase 3: Manual Match Selection Implementation

- [ ] Implement a new search endpoint that returns the top 5 match candidates from all providers.
- [ ] Design and implement the "Manual Match Selection" modal/component in the frontend.
- [ ] Implement logic to replace a degraded track with a manually selected alternative.
- [ ] Integration Test (Red/Green/Refactor): Verify a manual selection correctly
  updates the database and frontend state.
