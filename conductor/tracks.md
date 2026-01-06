# Product Tracks

## Active Track

None

## Backlog

### 1. Playlist Lifecycle & Sync Engine

- **Goal:** Make playlists robust with recovery options and bi-directional synchronization.
- **Key Features:**
  - Implement "Soft-Delete" for playlists with a 30-day auto-purge policy.
  - Import existing playlists from services.
  - Build the bi-directional sync engine (Periodic + On-Demand).

### 2. Advanced Metadata & Matching Intelligence

- **Goal:** Improve match quality and provide transparency when tracks are missing.
- **Key Features:**
  - Fix missing artist/album metadata in the modal (currently showing dashes).
  - Integrate Discogs as a secondary data source to reduce "degraded signals".
  - UI for "Degraded Signals" (explain why a track wasn't added).
  - Implement "Manual Match Selection" UI for ambiguous searches (show top 5 matches).

## Archive

- [x] **User Identity & Privacy** (2026-01-05)

- [x] **Foundation & Security Hygiene** (2026-01-04)

- [x] **Stabilize Core Services & Tests** (2026-01-02)
- [x] **Project Workspace Cleanup** (2026-01-04)
- [x] **Preemptive Formatting & Linting** (2026-01-04)
- [x] **Modern PostgreSQL Optimization** (2026-01-04)
