# Specification: Advanced Metadata & Matching Intelligence

This track aims to significantly improve the quality and transparency of track matching,
which is a key differentiator for Vibomat.

## Goals

1. **Reduce "Degraded Signals":** Use Discogs as a secondary metadata source to fill in gaps
   (missing artist/album info) where Spotify/MusicBrainz may fail.
2. **Improve User Trust:** Explicitly flag tracks where metadata remains incomplete or ambiguous
   ("Degraded Signals") to inform the user about potential match quality issues.
3. **Allow Manual Correction:** Provide a UI flow for users to manually select the correct track
   when the AI finds ambiguous matches, thus improving playlist quality post-generation.

## Implementation Details

### 1. Discogs Integration

- **New Client:** A new synchronous client (`DiscogsClient`) will be created in
  `backend/core/providers/discogs.py` (analogous to `SpotifyProvider`) to wrap the Discogs API.
- **Data Model:** The client must be able to search by artist/track and retrieve full metadata
  for verification.
- **Data Flow:** `MetadataVerifier` (or an updated service) should orchestrate calls: Spotify
  (primary) -> Discogs/MusicBrainz (secondary).

### 2. Degraded Signals

- **Flag Logic:** A track is a "degraded signal" if essential metadata (Artist, Album, Track Name)
  cannot be fully verified or located across multiple sources.
- **Frontend:** A clear, non-blocking indicator (e.g., a small caution icon) must appear next
  to the track in the playlist view.

### 3. Manual Match Selection

- **New Endpoint:** A new API endpoint (e.g., `/api/v1/metadata/search_candidates`) must be built
  that accepts fuzzy match data (artist, title, version) and returns a list of up to 5 structured
  track candidates from all available providers.
- **Frontend Flow:** When a track is flagged, the user can click an option to launch the match
  selection modal, interact with the new endpoint, and select a replacement track. This selection
  must trigger an update to the corresponding `Playlist` content.
