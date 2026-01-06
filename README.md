```markdown
# Vibomat

An intelligent, full-stack application to generate and manage music playlists using Generative AI
and external metadata verification.

## Core Features

- **AI Generation**: Describe a mood or theme (e.g., "Deep space ambient") and get a curated list.
- **Multi-Provider Verification**: Cross-references AI results with MusicBrainz and Discogs to
    eliminate hallucinations.
- **Service Sync**: Broadcast archives to Spotify and other major relays.
- **User Identity**: Implement User Identity, Handles, and Public Profiles

## Project Structure

```text
.
├── backend/            # FastAPI Series 2000
│   ├── app/            # Application Logic
│   └── core/           # Core Engines & CLI
├── frontend/           # React 19 + TanStack Series
└── conductor/          # Spec-Driven Framework
```

## Quick Start

1. **Boot Systems:** `docker compose up -d`
2. **Access Terminal:** `http://localhost:3000`
3. **Authentication:** Register and establish your Citizen ID.

## Developer Workflow

Vibomat uses the **Conductor** framework for spec-driven development.

1. **Select Track:** `conductor/tracks.md`
2. **Initialize Track:** `/conductor:implement track "<id>"`
3. **Execute Phase:** Follow the `plan.md` in sequential order.
4. **Verify & Checkpoint:** Automatic testing and linting required before phase completion.

## Quality Gates

- **Backend:** Pytest (>90% coverage required)
- **Frontend:** Vitest + React Testing Library
- **Static Analysis:** Ruff, Black, Ty (Type Checker)
- **Sanity Checks:** Playwright E2E verification

## Licensing

Vibomat is licensed under the MIT License. See `LICENSE` for details.
```