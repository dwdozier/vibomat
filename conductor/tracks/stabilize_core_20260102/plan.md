# Plan: Stabilize Core Functionality and MVP Release

This plan outlines the steps to stabilize the Vibomat MVP for initial release.

---

## Phase 1: Backend & Relay Stabilization [checkpoint: d3ebad3]

- [x] **Task 1: Audit Spotify Relay & Auth** <!-- 58b851b, 0d5f357 -->
  - [ ] Write tests for Spotify OAuth flow and relay synchronization.
  - [ ] Implement fixes for detected authentication or sync issues.
- [x] **Task 2: Verify Metadata Enrichment Service** <!-- 13e1012 -->
  - [ ] Write tests for MusicBrainz and Discogs verification logic.
  - [ ] Refactor `metadata_service.py` to handle edge cases and "no match" scenarios.
- [x] **Task 3: AI Service Prompt Optimization** <!-- da802cf -->
  - [ ] Write evaluation tests for AI-generated playlists.
  - [ ] Refine Gemini prompts to improve track relevance and metadata quality.
- [x] **Task 4: Conductor - User Manual Verification 'Backend & Relay Stabilization' (Protocol in
    workflow.md)**

---

## Phase 2: Playlist Management & UI Polish

- [x] **Task 1: AI-Powered Creative Naming** <!-- d7422c4 -->
  - [ ] Update `backend/core/ai.py` to request a "title" and "description" in the JSON response.
  - [ ] Update `backend/app/services/ai_service.py` to handle the new response structure.
  - [ ] Add tests for title generation.
- [~] **Task 2: Playlist Persistence & Tracking**
  - [ ] Verify `Playlist` model in `backend/app/models/playlist.py` supports tracking status
        (draft/transmitted).
  - [ ] Implement `create_playlist` and `update_playlist` endpoints to save AI results *before*
        Spotify transmission.
- [ ] **Task 3: Profile & Playlist View (Frontend)**
  - [ ] Create/Update `frontend/src/routes/profile.$userId.tsx` to list user's playlists
        (transmitted and drafts).
  - [ ] Implement a "Playlist Details" view (modal or page) to see tracks and metadata.
  - [ ] Add "Transmit to Spotify" button to the Playlist Details view.
- [ ] **Task 4: Thematic UI Polish**
  - [ ] Apply Art Deco borders and "Automat" styling to the new Playlist views.
- [ ] **Task 5: Conductor - User Manual Verification 'Playlist Management & UI Polish' (Protocol in
    workflow.md)**

---

## Phase 3: Release Readiness

- [ ] **Task 1: E2E Sanity Check**
  - [ ] Write Playwright tests for the full user journey (Citizen sign-up to Archive creation).
  - [ ] Fix any blockers discovered during E2E testing.
- [ ] **Task 2: Documentation & Docker Finalization**
  - [ ] Update `README.md` and `SETUP.md` with final instructions.
  - [ ] Verify production `docker-compose.prod.yml` configuration.
- [ ] **Task 3: Conductor - User Manual Verification 'Release Readiness' (Protocol in workflow.md)**
