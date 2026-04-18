## Why

The TravelAgent app currently has no user accounts, so users cannot save trips, preferences, or search history across sessions. Adding authentication enables personalization and sets the foundation for future user-specific features.

## What Changes

- New user registration and login flows (email + password)
- Session management via JWT tokens stored in HTTP-only cookies
- Protected routes that require authentication before accessing trip planning
- User profile endpoint returning basic account info
- Logout functionality to invalidate sessions

## Capabilities

### New Capabilities
- `user-auth`: Registration, login, logout, and session validation for users

### Modified Capabilities

## Impact

- **Backend**: New Flask routes (`/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`); new `User` model; JWT dependency added
- **Frontend**: Login/register modal or page; auth state tracked in JS; UI shows username when logged in
- **Dependencies**: `flask-jwt-extended` or `flask-login` + `bcrypt` for password hashing
- **Database**: SQLite (or existing store) gains a `users` table
