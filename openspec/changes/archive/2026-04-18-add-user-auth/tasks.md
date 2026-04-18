## 1. Dependencies & Configuration

- [x] 1.1 Add `flask-jwt-extended`, `flask-sqlalchemy`, and `bcrypt` to requirements.txt
- [x] 1.2 Add `JWT_SECRET_KEY` and `SQLALCHEMY_DATABASE_URI` to app config (read from env vars with fallback defaults)

## 2. Database & User Model

- [x] 2.1 Create `models.py` with a `User` model (id, email, password_hash, created_at)
- [x] 2.2 Initialize SQLAlchemy in `app.py` and call `db.create_all()` on startup

## 3. Auth Routes (Backend)

- [x] 3.1 Create `auth_routes.py` blueprint with `/auth/register` POST endpoint
- [x] 3.2 Add `/auth/login` POST endpoint with bcrypt password verification and JWT cookie response
- [x] 3.3 Add `/auth/logout` POST endpoint that clears the JWT cookie
- [x] 3.4 Add `/auth/me` GET endpoint (JWT-protected) returning `{ email, id }`
- [x] 3.5 Register the auth blueprint in `app.py`

## 4. Frontend – Auth Modal

- [x] 4.1 Add Login/Register modal HTML to `templates/index.html` with email, password fields and a toggle link
- [x] 4.2 Add CSS for the modal overlay to `static/css/style.css`
- [x] 4.3 Add JS in `static/js/app.js` to open/close the modal and toggle between Login and Register views

## 5. Frontend – Auth State & Header

- [x] 5.1 On page load, call `/auth/me` to check session; update header to show email + Logout or Login button
- [x] 5.2 Implement `handleLogin()` JS function: POST to `/auth/login`, update header on success
- [x] 5.3 Implement `handleRegister()` JS function: POST to `/auth/register`, auto-login on success
- [x] 5.4 Implement `handleLogout()` JS function: POST to `/auth/logout`, reset header to unauthenticated state

## 6. Validation & Error Handling

- [x] 6.1 Validate email format and password length (≥8 chars) on the backend `/auth/register` endpoint
- [x] 6.2 Return descriptive JSON error messages for 400/401/409 responses
- [x] 6.3 Show inline error messages in the modal on failed login/register

## 7. Testing

- [x] 7.1 Manually test registration with valid and duplicate emails
- [x] 7.2 Manually test login with correct and incorrect credentials
- [x] 7.3 Manually test logout and verify cookie is cleared
- [x] 7.4 Verify `/auth/me` returns 401 when unauthenticated and 200 when authenticated
- [x] 7.5 Verify header updates correctly for all auth state transitions
