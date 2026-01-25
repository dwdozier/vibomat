# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vibomat is an AI-powered universal music platform for generating and managing playlists. It uses
Generative AI (Google Gemini) for playlist creation and cross-references results with MusicBrainz
and Discogs for metadata verification. Currently supports Spotify integration with plans for
additional streaming services.

**Domain Terminology:** Users are "Citizens", playlists are "Archives", service connections are
"Relays", OAuth identity links are "Nodes", and unique social identifiers are "Handles".

## Commands

### Backend

```bash
# Run backend server
uv run uvicorn backend.app.main:app --reload

# Run TaskIQ worker (background tasks)
PYTHONPATH=. uv run taskiq worker backend.app.core.tasks:broker

# Run all tests with coverage (required >90%)
PYTHONPATH=. uv run pytest --cov=backend/core --cov=backend/app --cov-fail-under=90 backend/tests/ -m 'not ci'

# Run a single test file
PYTHONPATH=. uv run pytest backend/tests/test_api.py -v

# Run a specific test
PYTHONPATH=. uv run pytest backend/tests/test_api.py::test_function_name -v

# Type checking
uv run ty check
```

### Frontend

```bash
cd frontend

npm run dev       # Start Vite dev server
npm test          # Run Vitest
npm run lint      # ESLint
npm run build     # TypeScript check + Vite build
```

### Pre-commit & Linting

```bash
pre-commit install              # Install hooks (required)
pre-commit run --all-files      # Run all checks manually

# Individual tools
black .                         # Format Python
ruff check . --fix              # Lint Python
```

### Docker

```bash
docker-compose up --build       # Start all services with hot-reload
docker-compose down             # Stop and remove containers
```

### CLI Tool

```bash
vibomat build playlists/your-file.json
```

## Architecture

### Backend Structure (`backend/`)

- **`app/`** - FastAPI application
  - `api/v1/endpoints/` - REST endpoints (playlists, users, integrations, admin)
  - `models/` - SQLAlchemy models (User, Playlist, ServiceConnection, AILog, Metadata)
  - `schemas/` - Pydantic request/response schemas
  - `services/` - Business logic (ai_service, integrations_service, metadata_service)
  - `core/tasks.py` - TaskIQ background tasks (playlist sync, purge)
  - `db/` - Database session and migrations (Alembic)

- **`core/`** - CLI and standalone logic
  - `cli.py` - Typer CLI application
  - `client.py` - SpotifyPlaylistBuilder for API interaction
  - `ai.py` - Gemini AI integration for playlist generation
  - `metadata.py` - MusicBrainz/Discogs verification
  - `providers/` - Streaming service abstractions
    - `base.py` - `BaseMusicProvider` abstract class
    - `spotify.py` - Spotify implementation
    - `discogs.py` - Discogs implementation

### Frontend Structure (`frontend/src/`)

- **`routes/`** - TanStack Router file-based routes
- **`api/`** - API client functions
- **`components/`** - Reusable React components
- **`test/`** - Vitest tests

Uses TanStack Router with `loader` functions for data fetching. Avoid `useEffect` for data loading;
use TanStack Query or Router hooks instead.

### Key Patterns

- **Provider Pattern:** Music services implement `BaseMusicProvider` interface
- **Background Tasks:** TaskIQ with Redis for async operations (sync, purge)
- **Soft Delete:** Playlists use `deleted_at` timestamp, purged after 30 days
- **Auth:** FastAPI-Users with SQLAlchemy backend

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in
   `tech-stack.md` *before* implementation
3. **Test-Driven Development:** Write unit tests before implementing functionality (Red-Green-Refactor)
4. **High Code Coverage:** >90% code coverage required for all modules
5. **User Experience First:** Every decision should prioritize user experience
6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode
   tools (tests, linters) to ensure single execution.

## Task Workflow

When completing tasks in `plan.md`:

1. Mark task `[~]` when starting work
2. Write failing tests first (Red phase)
3. Implement minimum code to pass tests (Green phase)
4. Refactor if needed while tests pass
5. Mark task `[x]` when complete with commit SHA
6. Phase checkpoints require user manual verification

### Quality Gates

Before marking any task complete, verify:

- [ ] All tests pass
- [ ] Code coverage meets requirements (>90%)
- [ ] Code follows project style guidelines
- [ ] All public functions/methods have docstrings
- [ ] Type annotations present on all function signatures
- [ ] No linting or static analysis errors
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced

## Code Standards

- **Line Length:** 100 characters for Python and TypeScript (strictly enforced)
- **Python:** Black formatter, Ruff linter, Ty type checker, 4-space indentation
- **TypeScript:** ESLint, 2-space indentation, single quotes, trailing commas
- **Test Coverage:** >90% required for backend
- **E2E Testing:** Use `data-play` attributes for Playwright locators

### Critical Rules

**Code Quality:**

- Always call `.unique()` on SQLAlchemy results when using joined eager loads on collections
- Type annotations required for all function signatures
- Docstrings required for all functions and classes
- Wrap markdown text to 100 characters to prevent markdownlint failures
- Prefer TanStack Router `loader` functions over `useEffect` for data fetching
- Use `createRootRouteWithContext<T>()` and `Route.useRouteContext()` (not `Route.useContext()`)

**File Operations:**

- Never overwrite files without reading first; prefer incremental edits
- For files over 50 lines, always prefer incremental edits over full rewrites
- Preemptive formatting: write code that adheres to standards *before* saving (linters are
  validators, not fixers)

**Git Operations:**

- Never force push (rewrites history and disrupts collaboration)
- Never bypass branch protections or verification failures without explicit user approval
- Always use the Pull Request workflow unless specifically directed to push to `main`

## Conductor Workflow

This project uses spec-driven development tracked in `conductor/tracks.md`. Task progress is
recorded in `plan.md` files within each track directory. When completing tasks:

1. Mark task `[~]` when starting, `[x]` when complete with commit SHA
2. Run full test suite before marking complete
3. Phase checkpoints require user manual verification
