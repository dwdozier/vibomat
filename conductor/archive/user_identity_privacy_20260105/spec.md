# Specification: User Identity & Privacy

## 1. Extended User Model

- **Goal:** Support social features by expanding the user profile.
- **Requirements:**
  - Add `handle` (unique, user-settable string).
  - Add `first_name` and `last_name`.
  - Add `display_name` property logic: Handle > First Name > Username/Email.
  - Database migration to update `User` table.

## 2. Profile Visibility Controls

- **Goal:** Allow users to control who sees their profile.
- **Requirements:**
  - Add `is_public` (boolean) to User model.
  - API endpoint to toggle visibility.

## 3. "View As" Feature

- **Goal:** Allow users to preview their public profile.
- **Requirements:**
  - Endpoint to get public profile of a user (filtered data).
  - Frontend UI to toggle between "Edit Mode" and "Public View" on the profile page.
