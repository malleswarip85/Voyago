## ADDED Requirements

### Requirement: User Registration
The system SHALL allow a new user to register with a unique email address and a password. The password SHALL be stored as a bcrypt hash; plaintext passwords SHALL never be persisted.

#### Scenario: Successful registration
- **WHEN** a user submits a valid email and password (minimum 8 characters)
- **THEN** the system creates a new user record, returns HTTP 201, and issues a JWT cookie

#### Scenario: Duplicate email registration
- **WHEN** a user submits an email that already exists in the database
- **THEN** the system returns HTTP 409 with an error message "Email already registered"

#### Scenario: Invalid password
- **WHEN** a user submits a password shorter than 8 characters
- **THEN** the system returns HTTP 400 with an error message "Password must be at least 8 characters"

### Requirement: User Login
The system SHALL authenticate a user by verifying their email and bcrypt-hashed password. On success, a JWT SHALL be set as an HTTP-only cookie.

#### Scenario: Successful login
- **WHEN** a user submits a correct email and password
- **THEN** the system returns HTTP 200, sets a JWT in an HTTP-only cookie, and returns the user's email

#### Scenario: Wrong password
- **WHEN** a user submits a correct email but incorrect password
- **THEN** the system returns HTTP 401 with "Invalid credentials"

#### Scenario: Unknown email
- **WHEN** a user submits an email not in the database
- **THEN** the system returns HTTP 401 with "Invalid credentials"

### Requirement: User Logout
The system SHALL allow an authenticated user to invalidate their session by clearing the JWT cookie.

#### Scenario: Successful logout
- **WHEN** an authenticated user calls the logout endpoint
- **THEN** the system clears the JWT cookie and returns HTTP 200

### Requirement: Session Validation
The system SHALL expose an endpoint that returns the current user's info if a valid JWT cookie is present, enabling the frontend to determine auth state on page load.

#### Scenario: Valid session
- **WHEN** a request arrives with a valid, non-expired JWT cookie
- **THEN** the system returns HTTP 200 with `{ "email": "<user_email>", "id": <user_id> }`

#### Scenario: No or expired session
- **WHEN** a request arrives with no JWT cookie or an expired JWT
- **THEN** the system returns HTTP 401

### Requirement: Frontend Auth Modal
The system SHALL display a login/register modal when the user is unauthenticated and clicks "Login", and SHALL display the logged-in user's email and a "Logout" button in the header when authenticated.

#### Scenario: Unauthenticated header state
- **WHEN** the page loads and no valid session exists
- **THEN** the header shows a "Login" button and no username

#### Scenario: Authenticated header state
- **WHEN** the page loads and a valid session exists
- **THEN** the header shows the user's email and a "Logout" button

#### Scenario: Login modal opens
- **WHEN** an unauthenticated user clicks "Login"
- **THEN** a modal appears with email/password fields and a toggle to switch to Register
