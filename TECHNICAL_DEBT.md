# Technical Debt & Next Steps

This document tracks recommended improvements and technical debt items for the Vibomat project.

**Last Updated**: January 27, 2026

---

## Recently Completed ✅

### Backend Security & Error Handling Improvements (PR #106)

Completed comprehensive security overhaul addressing 8 critical vulnerabilities:

- ✅ Custom exception hierarchy with proper error types
- ✅ Structured JSON logging with request correlation
- ✅ Distributed locking for token refresh (Redis-based)
- ✅ Access token encryption at rest (Fernet)
- ✅ Rate limiting on public endpoints (slowapi)
- ✅ Input validation for playlist content_json
- ✅ Error message sanitization to prevent information leakage
- ✅ ProxyHeaders security configuration
- ✅ Refactored all generic Exception handlers

**Test Coverage**: Maintained >90% (added 1,500+ lines of tests)

**Files Modified**: 22 files (8 new, 8 modified, 6 new test files)

### Infrastructure Fixes (PRs #107, #109)

- ✅ Doc-agent merge conflicts fixed with fresh-branch strategy
- ✅ Dependabot python-multipart ignore configured (waiting for upstream)

---

## Recommended Next Steps

The following technical debt categories were identified during the security audit and should be
addressed in priority order:

### 1. Configuration & Infrastructure Cleanup

**Priority**: Medium
**Effort**: 4-6 hours

#### Issues

- **Line length conflicts**: Code enforces 100 chars but some configs reference 120
  - `pyproject.toml`: `line-length = 100`
  - `.pre-commit-config.yaml`: Some tools may use different values
  - Ruff, Black, ESLint need alignment

- **README.md updates**: Ensure reflects current state post-security work
  - Update troubleshooting section if needed
  - Verify Quick Start is accurate
  - Check that Core Features list is current

- **Missing tech-stack.md**: No centralized documentation of technology choices
  - Backend: FastAPI, SQLAlchemy, Alembic, TaskIQ, Redis, PostgreSQL, pgvector
  - Frontend: React 19, TanStack Router, TanStack Query, Vite, TypeScript
  - Infrastructure: Docker, GitHub Actions, uv, Playwright
  - AI/Metadata: Google Gemini, MusicBrainz, Discogs, Spotify API

#### Action Items

- [ ] Audit all linting configs for line-length consistency
- [ ] Create comprehensive tech-stack.md with rationale for each choice
- [ ] Review and update README.md for accuracy
- [ ] Document configuration standards in CLAUDE.md

---

### 2. Frontend Testing & Error Handling

**Priority**: High
**Effort**: 12-16 hours

#### Issues

- **Low test coverage**: Frontend has minimal test coverage compared to backend (>90%)
  - Missing tests for critical user flows
  - No integration tests for API interactions
  - Component tests incomplete

- **Error boundaries missing**: React components lack proper error handling
  - Unhandled API errors can crash entire UI
  - No fallback UI for error states
  - Error messages not user-friendly

- **API client improvements needed**:
  - No retry logic for transient failures
  - No request cancellation on component unmount
  - Missing timeout configuration
  - Error responses not properly typed

#### Action Items

- [ ] Implement React Error Boundaries for major component trees
- [ ] Add retry logic to API client with exponential backoff
- [ ] Create standardized error response types
- [ ] Write integration tests for critical user flows:
  - [ ] Authentication flow
  - [ ] Playlist creation/editing
  - [ ] Spotify integration
  - [ ] Metadata search
- [ ] Add Vitest coverage requirements (target: >80%)
- [ ] Implement request cancellation in TanStack Query

#### Files to Create/Modify

- `frontend/src/components/ErrorBoundary.tsx` (NEW)
- `frontend/src/api/client.ts` - Add retry and timeout logic
- `frontend/src/api/types.ts` - Standardize error types
- `frontend/src/test/` - Add integration tests

---

### 3. Database Optimization

**Priority**: Medium
**Effort**: 8-12 hours

#### Issues

- **Missing indexes**: Query performance can degrade as data grows
  - Playlist searches on `user_id`, `deleted_at`
  - AI interaction lookups on `user_id`, `created_at`
  - Service connections on `user_id`, `provider_name`
  - Metadata searches need FTS indexes

- **N+1 query problems**: Identified in several endpoints
  - Playlist list endpoint loads tracks separately
  - User profile loads all service connections separately
  - AI logs lack proper eager loading

- **Inconsistent soft delete**: Not all models properly implement soft delete pattern
  - Some queries don't filter `deleted_at IS NULL`
  - Cascade behavior unclear on soft-deleted records
  - Purge task only handles playlists, not other models

#### Action Items

- [ ] Database index audit:
  - [ ] Add index on `playlists(user_id, deleted_at)`
  - [ ] Add index on `ai_interaction_embeddings(user_id, created_at)`
  - [ ] Add index on `service_connections(user_id, provider_name)`
  - [ ] Review query logs to identify other slow queries
- [ ] Fix N+1 queries:
  - [ ] Use `selectinload()` for playlist tracks in list endpoint
  - [ ] Eager load service connections on user profile
  - [ ] Add `joinedload()` where appropriate
- [ ] Standardize soft delete:
  - [ ] Create base soft-delete mixin
  - [ ] Document soft-delete policy in ARCHITECTURE.md
  - [ ] Extend purge task to all soft-deletable models
  - [ ] Add database constraints to enforce pattern

#### Files to Create/Modify

- `backend/app/models/base.py` - Soft delete mixin (NEW)
- `backend/app/db/migrations/versions/` - Add indexes migration
- `backend/app/api/v1/endpoints/playlists.py` - Fix N+1 queries
- `backend/app/core/tasks.py` - Extend purge task
- `ARCHITECTURE.md` - Document soft delete pattern (NEW)

---

## Additional Observations

### Documentation Gaps

- Missing ARCHITECTURE.md explaining overall system design
- No API documentation (consider OpenAPI/Swagger UI)
- Conductor workflow could use more examples
- Missing troubleshooting guide for common dev issues

### Code Quality

- Some files exceed 300 lines (consider splitting):
  - `backend/app/api/v1/endpoints/playlists.py` (>500 lines)
  - `backend/app/services/integrations_service.py` (>200 lines)
- Duplicate code in API endpoint error handling (now somewhat mitigated by exception handler)

### Performance

- No caching layer (consider Redis caching for metadata lookups)
- Spotify API rate limiting could be more sophisticated
- Vector similarity search (pgvector) not optimized with HNSW index

---

## How to Use This Document

When starting a new coding session:

1. **Check "Recently Completed"** to see what's been done
2. **Pick a priority area** from "Recommended Next Steps"
3. **Create a new branch** from main: `git checkout -b feature/description`
4. **Follow TDD**: Write tests first, then implementation
5. **Update this document** when items are completed

When completing work:

1. Move completed items from "Next Steps" to "Recently Completed"
2. Add PR number and completion date
3. Note any new technical debt discovered during implementation

---

## Notes

- All changes must maintain >90% test coverage for backend
- Frontend changes should target >80% test coverage
- Follow existing patterns in CLAUDE.md
- Update CHANGELOG.md via conventional commits (handled by release-please)
