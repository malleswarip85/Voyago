## Context

The TravelAgent app is a Flask + vanilla-JS single-page app backed by SerpAPI for flights and hotels. There is currently no persistence layer beyond in-memory state. Adding auth introduces the first database model and session management to the stack.

## Goals / Non-Goals

**Goals:**
- Email + password registration and login
- Secure password storage with bcrypt hashing
- JWT-based session management via HTTP-only cookies
- Protected API routes that reject unauthenticated requests
- Minimal frontend changes: login/register modal, username display in header, logout button

**Non-Goals:**
- OAuth / social login (Google, GitHub, etc.)
- Email verification or password reset flows
- Role-based access control
- Rate limiting on auth endpoints (future work)

## Decisions

### 1. JWT in HTTP-only cookies vs. localStorage
**Decision**: Store JWT in an HTTP-only cookie.
**Rationale**: HTTP-only cookies are not accessible via JavaScript, preventing XSS token theft. localStorage is simpler but vulnerable to XSS attacks, which is unacceptable for auth tokens.
**Alternative considered**: `Authorization: Bearer` header with localStorage — rejected due to XSS risk.

### 2. flask-jwt-extended vs. flask-login
**Decision**: Use `flask-jwt-extended`.
**Rationale**: Stateless JWTs work well with the existing API-centric architecture. `flask-login` is session-cookie based and requires server-side session storage. JWT tokens can be verified without a DB lookup on every request.
**Alternative considered**: `flask-login` with server-side sessions — rejected because it requires additional session storage and doesn't align with the API model.

### 3. Database: SQLite via SQLAlchemy
**Decision**: Introduce SQLite with Flask-SQLAlchemy for the `users` table.
**Rationale**: The app has no existing DB. SQLite is zero-config and sufficient for single-user or low-concurrency use. SQLAlchemy makes future migration to Postgres straightforward.
**Alternative considered**: JSON file store — rejected because it doesn't handle concurrent writes safely.

### 4. Frontend: modal overlay vs. separate page
**Decision**: Login/register as a modal overlay.
**Rationale**: Keeps the single-page feel; no routing changes needed. The modal is shown when an unauthenticated user tries to search or when they click "Login".

## Risks / Trade-offs

- **JWT secret rotation** → If the JWT secret changes, all existing tokens are invalidated. Mitigation: document secret in env var `JWT_SECRET_KEY`; use a long random value.
- **SQLite concurrency** → Not suitable for high-concurrency production. Mitigation: acceptable for current scale; SQLAlchemy makes future migration easy.
- **CSRF on cookie-based JWT** → HTTP-only cookies are vulnerable to CSRF. Mitigation: `flask-jwt-extended` supports CSRF double-submit protection; enable it.
- **No email verification** → Fake emails can register. Mitigation: deferred to future work; acceptable for MVP.

## Migration Plan

1. Install new dependencies (`flask-jwt-extended`, `flask-sqlalchemy`, `bcrypt`).
2. Initialize DB with `db.create_all()` on app startup — creates `users` table if absent.
3. Deploy alongside existing routes; no existing routes are broken.
4. Rollback: remove auth blueprint and DB init; no data migration needed since feature is additive.

## Open Questions

- Should unauthenticated users still be able to search (guest mode), or must they log in first?
  - **Assumption**: Guest search is allowed; login is optional but required to save trips in future.
