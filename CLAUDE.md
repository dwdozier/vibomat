# CLAUDE.md

## Project Context

Vibomat: AI-powered music platform. Reference docs (read on-demand, not preloaded):

- `conductor/product.md` - Vision, audience, differentiators
- `conductor/product-guidelines.md` - Art Deco visual identity, color palette, UX
- `conductor/tech-stack.md` - Full stack details and troubleshooting

**Domain terms:** Users = "Citizens", playlists = "Archives", service connections =
"Relays", OAuth links = "Nodes", social IDs = "Handles".

## Commands

Use `make help` to see all targets. Key commands:

```bash
# Backend
make test                    # Unit tests (excludes CI-only)
make test-cov                # Tests with coverage (>90% required)
PYTHONPATH=. uv run pytest backend/tests/test_file.py::test_name -v  # Single test

# Frontend (from frontend/)
npm test                     # Vitest
npm run build                # TypeScript check + Vite build

# Quality
pre-commit run --all-files   # All hooks (black, ruff, ty, markdownlint, tests)
uv run ty check              # Type checking
```

## Code Standards

- **Python line length:** 120 characters (Black + Ruff, per `pyproject.toml`)
- **Markdown line length:** 100 characters (per `.markdownlint.json`)
- **Test coverage:** >90% required for backend (`--cov-fail-under=90`)
- **E2E locators:** Use `data-play` attributes for Playwright
- Write compliant code from the start; linters are validators, not fixers

## Critical Rules

These are easy to get wrong. Follow them exactly:

- Always call `.unique()` on SQLAlchemy results with joined eager loads on
  collections
- Use TanStack Router `loader` functions, not `useEffect`, for data fetching
- Use `createRootRouteWithContext<T>()` and `Route.useRouteContext()` (not
  `Route.useContext()`)
- Playlists use soft delete (`deleted_at` timestamp), purged after 30 days
- Tech stack changes must be documented in `tech-stack.md` before implementation

## Commits

Use conventional commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Task Workflow

Development tracked in `conductor/tracks.md` with `plan.md` files per track.

1. Mark task `[~]` when starting, write failing tests first (TDD)
2. Implement minimum code to pass, refactor while green
3. Verify: tests pass, coverage >90%, no lint/type errors, docstrings present
4. Mark task `[x]` with commit SHA
5. Phase checkpoints require user manual verification
