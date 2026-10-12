<span style="font-family: 'Roboto', monospace; font-size: 16px;">

# Wireframes

### Test page:
![Wireframe design for the test page](wireframe-testpage.png "Wireframe design for the test page")

# Logo

![Company logo](logo.svg "Company Logo")

# Color Palette

We chose a sea theme, to reflect Weston's coastal history:

![Colour palette for the website](colour-palette.png "Colour palette for the website")

The associated Hex Codes for these colours are:
```
#0047AB
#6495ED
#89CFF0
#6082B6
#B6D0E2
```

# Entity Relationship Diagram (ERD)

![Entity Relationship Diagram](ERD.png "Entity Relationship Diagram")

# Font

### Roboto

This is the HTML code to get the chosen roboto font into our website
```
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
```
Alternatively, the CSS to get roboto into our website is:
```
.roboto-<uniquifier> {
  font-family: "Roboto", sans-serif;
  font-optical-sizing: auto;
  font-weight: <weight>;
  font-style: normal;
  font-variation-settings:
    "wdth" 100;
}
```
# REST Endpoints

Proposed API surface derived from the platform requirements (landing page, auth, student registration, student dashboard). Registration, approval, rejection, and test assignment are explicit action routes for clarity; MFA/password-reset deferred to a later phase.

## MVP endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Single login for all roles |
| `POST` | `/api/auth/logout` | Invalidate current session/token |

### Users (students, lecturers, admins)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/users/register` | Student self-registration (public; creates `role=student`, `status=pending`) |
| `GET` | `/api/users?role=&status=` | List/filter users (e.g., lecturer viewing pending students) |
| `GET` | `/api/users/{id}` | Get a user's profile |
| `PATCH` | `/api/users/{id}` | Update a user's profile fields (role-gated) |
| `POST` | `/api/users/{id}/approve` | Lecturer approves a pending student registration |
| `POST` | `/api/users/{id}/reject` | Lecturer rejects a pending student registration |
| `DELETE` | `/api/users/{id}` | Deactivate/delete a user (admin-only) |

### Tests

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tests` | List tests visible to the authenticated user (assigned tests for students, authored tests for lecturers) |
| `POST` | `/api/tests` | Create a test (lecturer-only) |
| `PATCH` | `/api/tests/{id}` | Update a test's own fields (lecturer-only) |
| `POST` | `/api/tests/{id}/assign` | Assign a test to one or more students (lecturer-only) |
| `DELETE` | `/api/tests/{id}` | Delete a test (lecturer-only) |

### Questions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/questions` | List question bank |
| `POST` | `/api/questions` | Create a question (lecturer-only) |
| `PATCH` | `/api/questions/{id}` | Update a question (lecturer-only) |

### Attempts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/tests/{id}/attempts` | Student starts an attempt |
| `PATCH` | `/api/tests/{id}/attempts/{attempt_id}` | Submit/update answers, or fetch result via `GET` |

### Pages (server-rendered)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Landing page ([home.py](../rest/home.py)) |
| `GET` | `/login` | Login page (single form for all roles) |
| `GET` | `/register` | Student registration page |
| `GET` | `/dashboard` | Student dashboard - test selection |
| `GET` | `/tests/{id}` | Test-taking page for an active attempt |
| `GET` | `/lecturer/dashboard` | Lecturer dashboard - pending approvals, test/question management |

## Post MVP (additional functionality)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/mfa/challenge` | Send OTP (email/SMS/authenticator app) |
| `POST` | `/api/auth/mfa/verify` | Verify OTP to complete login |
| `POST` | `/api/auth/password/forgot` | Request password reset |
| `POST` | `/api/auth/password/reset` | Complete password reset with token |

## Notes

- Role-based access (`student`, `lecturer`, `admin`) enforced per-endpoint in the REST layer per this repo's clean-architecture convention (REST → use cases → database).
- `DELETE` on questions omitted from MVP — question bank items are typically soft-retired (e.g., `status=archived` via `PATCH`) rather than hard-deleted once used in a test.

</span>
