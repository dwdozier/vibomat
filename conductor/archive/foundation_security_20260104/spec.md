# Specification: Foundation & Security Hygiene

## 1. Configuration Management

- **Goal:** Differentiate between Dev and Prod configuration and ensure all secrets are accounted for.
- **Requirements:**
  - Audit `backend/app/core/config.py` and `.env` usage.
  - Create a verified `.env.example` that lists ALL required keys for production.
  - Create a `.env.development` (or keep existing) that provides sensible defaults for local dev.
  - Ensure the application fails fast if critical production keys are missing.

## 2. OAuth Scope Transparency

- **Goal:** Show users exactly what permissions we are requesting from services (e.g., Spotify).
- **Requirements:**
  - "Relay Station" UI (Connections page) must list the specific scopes granted for each connection.
  - Backend must verify scopes are actually granted and store/return them via the API.
  - **Security:** Ensure we only request the minimum necessary scopes for the features we
    need (read playlists, modify public playlists, etc.).

## 3. Session Security & Auth Guards

- **Goal:** Prevent unauthorized access and handle session expiry gracefully.
- **Requirements:**
  - **Frontend:**
    - Global Auth Guard for protected routes.
    - Intercept 401/403 responses globally and redirect to Login.
    - If a user tries to access a protected URL (e.g., `/playlists/123`) without a session,
      redirect to Login, then *back* to the intended URL after success.
  - **Backend:**
    - Ensure all protected endpoints strictly enforce `current_user` dependencies.
    - Verify token expiration logic is working correctly.
