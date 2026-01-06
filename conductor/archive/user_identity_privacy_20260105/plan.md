# Plan: User Identity & Privacy

## Phase 1: Backend - User Model Expansion

- [x] Create DB migration to add `handle`, `first_name`, `last_name`, `is_public` to `User` table.
- [x] Update `User` SQLAlchemy model and Pydantic schemas.
- [x] Implement `handle` uniqueness check and validation logic.
- [x] Update API endpoints (`/users/me`) to support updating these fields.
- [x] Add `display_name` property to User model/schema.

## Phase 2: Frontend - Profile Management

- [x] Update Profile Page UI to include form fields for Name and Handle.
- [x] Implement validation for Handle (debounce check against API).
- [x] Add Visibility Toggle (Public/Private) to Profile settings.

## Phase 3: Public Profile & "View As"

- [x] Create `/users/{handle}` public endpoint (respecting `is_public`).
- [x] Create Public Profile Page in frontend.
- [x] Add "View Public Profile" button for the logged-in user.

## Phase 4: Verification

- [x] Run full backend test suite (`test_auth.py`, `test_social.py`).
- [x] Manual verification of Profile updates and Public View.
