# Plan: Refactoring & Tech Debt

## Phase 1: Test Suite Hardening

- [ ] Refactor tests to use a robust `override_dependencies` fixture that guarantees cleanup
  (try/finally or yield).
- [ ] Audit all tests for "testing 3rd party libraries" and mock them out (e.g. `spotipy` calls in
  `SpotifyProvider`).
- [ ] Fix dependency leaks in `backend/tests/conftest.py` if any (ensure global state is reset).

## Phase 2: Codebase Simplification

- [ ] Review `backend/core/providers/spotify.py` for complexity and unused methods.
- [ ] Standardize API status codes (e.g. `POST /playlists` should return 201 Created).
- [ ] Remove unused "extra" test files if they can be merged into main test files cleanly.

## Phase 3: Developer Experience

- [ ] Ensure local development environment (Docker) matches CI environment exactly.
- [ ] Add `make test` or similar command to run tests with correct environment variables and coverage.
