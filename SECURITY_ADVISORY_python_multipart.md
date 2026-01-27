# Security Advisory: python-multipart Dependency

## Current Situation

**Date**: January 27, 2026

### Issue

We are currently using `python-multipart==0.0.21` (via
`fastapi-users[sqlalchemy]==15.0.3`), which is one version behind the latest release `0.0.22`
(released January 25, 2026).

### Why We Can't Update Yet

`fastapi-users==15.0.3` (latest) has a **strict pin** on `python-multipart==0.0.21` in its
dependencies. Attempting to update python-multipart to 0.0.22 causes dependency resolution
failures:

```text
Because fastapi-users==15.0.3 depends on python-multipart==0.0.21
and your project depends on python-multipart>=0.0.22,
we can conclude that your project's requirements are unsatisfiable.
```

### Upstream Status

- **PR #1560** opened in fastapi-users repository on January 26, 2026
- URL: <https://github.com/fastapi-users/fastapi-users/pull/1560>
- Status: OPEN (awaiting merge and release)
- This PR updates python-multipart from 0.0.21 to 0.0.22

### What We Changed

1. **Configured Dependabot to ignore python-multipart updates** (in `.github/dependabot.yml`)
   - This stops Dependabot from creating failing PRs
   - Added tracking link to upstream PR

2. **Documented the security posture** (this file)

### What's the Risk?

The changelog for python-multipart 0.0.22 shows:

- "Drop directory path from filename in File"
- This appears to be a **security fix** for path traversal vulnerability

**Impact**: LOW to MEDIUM

- We don't currently use file upload features extensively
- All file uploads go through FastAPI validation
- Application runs in Docker containers with limited filesystem access

### Action Items

- [ ] Monitor <https://github.com/fastapi-users/fastapi-users/pull/1560>
- [ ] When PR merges, update to new fastapi-users version
- [ ] Remove python-multipart ignore from dependabot.yml
- [ ] Delete this advisory

### How to Check Status

```bash
# Check if fastapi-users has released new version supporting python-multipart 0.0.22
pip index versions fastapi-users

# If new version available, update:
uv pip install --upgrade fastapi-users
uv lock
git diff pyproject.toml uv.lock  # Verify changes
```
