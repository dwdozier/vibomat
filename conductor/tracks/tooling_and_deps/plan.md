# Plan: Tooling & Dependencies

## Phase 1: Frontend Tooling

- [ ] Audit `tsconfig` files (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`) and
  unify/simplify if possible.
- [ ] Ensure `npm run build` cleanly handles all environments (dev/prod/test).
- [ ] Fix E2E test types (`@playwright/test`) to allow including them in linting/checking.

## Phase 2: Docker Optimization

- [ ] optimize `backend/Dockerfile` and `frontend/Dockerfile` for caching (already partially done,
  but verify layers).
- [ ] Review `docker-compose` vs `docker-compose.override` usage to ensure clarity between dev and
  prod setups.

## Phase 3: Pre-commit Hooks

- [ ] Audit `pre-commit` hooks for performance (running `npm install` inside hooks? verify).
- [ ] Ensure all linters (ruff, eslint) share config with IDE settings.
