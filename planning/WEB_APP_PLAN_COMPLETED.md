# Web Application Transition Plan

This document outlines the phased approach to transforming the `spotify-playlist-builder` CLI tool
into a full-stack, multi-provider web application.

## 1. Vision

To create a hosted, multi-user web application that allows users to generate, manage, and sync
playlists across potentially multiple streaming services (Spotify, Apple Music, etc.) using AI and
external metadata verification.

## 2. Technical Stack

* **Backend:** Python (FastAPI).

* **Database:** PostgreSQL (Production) / SQLite (Dev) with SQLAlchemy (Async) + Alembic.

* **Frontend:** React (TypeScript) via **Vite** + **TanStack Router** + **TanStack Query**.

* **Auth (Identity):** OAuth2 (Google/GitHub) via `fastapi-users` or similar.

* **Auth (Integrations):** Custom OAuth2 flows for linking Streaming Services (Spotify, etc.).
* **Infrastructure:** Docker, Docker Compose.
* **Testing:**
  * **Backend:** `pytest`, `pytest-cov` (Unit/Integration).
  * **Frontend:** `Vitest` + `React Testing Library` (Component Logic).
  * **E2E:** `Playwright` (Python via `pytest-playwright`) for Critical User Journeys.

## 3. Implementation Phases

### Phase 1: API Foundation (FastAPI)

**Goal:** Expose core logic via a REST API with high test coverage.

* [x] **Project Restructure:** Create `backend/` and `frontend/`. Move existing logic to
    `backend/core/`.
* [x] **FastAPI Setup:** Initialize `backend/app/main.py`.
* [x] **Dependency Injection:** Refactor `SpotifyPlaylistBuilder` and `MetadataVerifier` into
    injectable services.
* [x] **Endpoints - Health:** `/health` endpoint.
* [x] **Endpoints - AI Generation:** `POST /api/generate` (agnostic of streaming service).
* [x] **Endpoints - Verification:** `POST /api/verify` (agnostic metadata verification).
* [x] **Testing:** Add `pytest` integration tests for all endpoints. **Target: 95% Backend
    Coverage.**

### Phase 2: Database, Identity & Service Linking

**Goal:** Decouple "User Identity" from "Streaming Service Integration".

* [x] **Database Setup:** Configure Async SQLAlchemy & Alembic.

* [x] **Identity System:**

  * Implement generic User Login (Google/GitHub/Email).

  * Create `User` model.

* [x] **Service Connection System:**

  * Create `ServiceConnection` model.

  * Implement "Connect Spotify" OAuth flow.

* [x] **Playlist Persistence:**

  * Create `Playlist` model.

* [x] **Testing:** Integration tests for DB models, Auth flows (mocked), and Token refreshing.

### Phase 3: Web Frontend (MVP) & Component Testing

**Goal:** A functional UI with component-level testing.

* [x] **Frontend Setup:** Initialize React/TanStack project.

* [x] **Auth UI:** Login page & "Connections" Settings page.

* [x] **Dashboard:** List user's saved playlists (Placeholder UI).

* [x] **Generator:** Form for AI prompts & Interactive Verification/Review list.

* [x] **Build/Sync:** Select *Connected Service* to push to (UI logic).

* [x] **Testing:** Unit tests for complex components (Review List, Auth Hooks). **Target: 95%

    Logic Coverage.**

### Phase 4: E2E Testing & Advanced Features

**Goal:** Production readiness and full functional verification.

* [x] **E2E Setup:** Configure `Playwright` (Python).

* [x] **Multi-Provider Support:** Add abstractions (`BaseMusicProvider`) and `SpotifyProvider`.

* [x] **Import/Export:** API endpoint for JSON export.

* [x] **Discogs Integration:** API endpoint for managing Discogs PAT.

* [x] **E2E Tests:** Implement Critical User Journeys (CUJs).

* [x] **Background Tasks:** TaskIQ/Redis for long-running builds.

### Phase 5: Infrastructure & Deployment

**Goal:** Host the application.

* [x] **Docker:** Optimized multi-stage builds for Backend and Frontend.

* [x] **Docker Compose:** Full local stack (App, DB, Redis).

* [x] **CI/CD:** GitHub Actions (Lint, Test Backend, Test Frontend). Enforce 95% coverage.

* [ ] **Deployment:** Reference configs for cloud providers.

## 4. Quality Assurance Guidelines

* **Coverage:** 95% minimum for Backend and Frontend logic.
* **Philosophy:** Test *behavior*, not implementation details.
* **E2E:** Focus on happy paths and critical failure modes (e.g., API down). Avoid testing
    third-party login pages directly (mock the auth success callback).

## 5. CLI Evolution & Parity

While the focus is on the Web Application, the CLI remains a first-class interface:

* **Current State:** CLI interacts directly with `backend.core` logic.
* **Future Goal:** Refactor CLI commands to act as a thin client for the FastAPI API. This ensures
    unified logic and allows the CLI to work against remote hosted instances.
* **Timeline:** This refactor will be scheduled for Phase 4 (Advanced Features & Polish).

## 6. Immediate Next Steps

1. **Approval:** Confirm this plan.
2. **Phase 1:** Begin structure refactor.
