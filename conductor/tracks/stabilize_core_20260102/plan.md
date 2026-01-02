# Plan: Stabilize Core Functionality and MVP Release

This plan outlines the steps to stabilize the Vibomat MVP for initial release.

---

## Phase 1: Backend & Relay Stabilization

- [x] **Task 1: Audit Spotify Relay & Auth** <!-- 58b851b -->
  - [ ] Write tests for Spotify OAuth flow and relay synchronization.
  - [ ] Implement fixes for detected authentication or sync issues.
- [x] **Task 2: Verify Metadata Enrichment Service** <!-- 13e1012 -->
  - [ ] Write tests for MusicBrainz and Discogs verification logic.
  - [ ] Refactor `metadata_service.py` to handle edge cases and "no match" scenarios.
- [x] **Task 3: AI Service Prompt Optimization** <!-- da802cf -->
  - [ ] Write evaluation tests for AI-generated playlists.
  - [ ] Refine Gemini prompts to improve track relevance and metadata quality.
- [ ] **Task 4: Conductor - User Manual Verification 'Backend & Relay Stabilization' (Protocol in workflow.md)**

---

## Phase 2: Frontend Polishing & UI/UX

- [ ] **Task 1: Thematic UI Audit**
  - [ ] Write Vitest snapshots for core components (`DataTable`, `Modal`).
  - [ ] Apply Art Deco borders and "Automat" styling according to `product-guidelines.md`.
- [ ] **Task 2: State Management & Error Handling**
  - [ ] Write tests for TanStack Query error boundaries and loading states.
  - [ ] Implement consistent error notifications for Citizens when a Relay fails.
- [ ] **Task 3: Conductor - User Manual Verification 'Frontend Polishing & UI/UX' (Protocol in workflow.md)**

---

## Phase 3: Release Readiness

- [ ] **Task 1: E2E Sanity Check**
  - [ ] Write Playwright tests for the full user journey (Citizen sign-up to Archive creation).
  - [ ] Fix any blockers discovered during E2E testing.
- [ ] **Task 2: Documentation & Docker Finalization**
  - [ ] Update `README.md` and `SETUP.md` with final instructions.
  - [ ] Verify production `docker-compose.prod.yml` configuration.
- [ ] **Task 3: Conductor - User Manual Verification 'Release Readiness' (Protocol in workflow.md)**
