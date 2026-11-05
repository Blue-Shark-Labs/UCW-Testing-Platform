<span style="font-family: 'Roboto', monospace; font-size: 16px;">

# Mockup

### Test page:
![Mockup design for the test page](mockup-testpage.png "Mockup design for the test page")
 
# Logo

Blue shark labs logo:

<img src="logo.jpeg" alt="Company logo" width="200"/>

# Colour Palette

We chose a sea theme, to reflect Weston's coastal history:

<img src="colour-palette.png" alt="Colour palette for the website" width="200"/>

The associated Hex Codes for these colours are:
```
#0047AB
#6495ED
#89CFF0
#6082B6
#B6D0E2
```
Colours #0047AB, #6082B6, #B6D0E2 have been chosen to match the WCAG 2.2 AA requirements of 4.5:1 contrast ratio when paired with either white text or black text, white text for dark colours, black text for light colours. The other 2 colours are there for variety within the UI, but will not have text on top of them.

# Entity Relationship Diagram (ERD)

<img src="ERD.png" alt="Entity Relationship Diagram" width="1080"/>

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

# Key Flowcharts

## 1. Guest Landing → Auth Entry

Covers FR-01 to FR-04.

```mermaid
flowchart TD
    A[Guest opens platform] --> B[Landing page loads<br/>fonts/styles applied - FR-01]
    B --> C{Guest action}
    C -->|Click Login| D[Login view - FR-02]
    C -->|Click Sign Up| E[Sign-up view - FR-03]
    C -->|Click Product Info| F[View product info - FR-04]
    C -->|Click Contact Info| G[View contact info - FR-03]
```

## 2. Authentication & Session Flow

Covers FR-05 to FR-11, FR-012, NFR-03, NFR-05, NFR-06.

```mermaid
flowchart TD
    A[User on login page<br/>username + password - FR-06...08] --> B[Submit credentials]
    B --> C{Input valid? - NFR-06}
    C -->|No| D[Show validation error]
    D --> A
    C -->|Yes| E{Account locked from<br/>10+ attempts? - FR-11}
    E -->|Yes| F[Reject login<br/>show lockout message]
    E -->|No| G{Credentials match<br/>hashed password? - NFR-03}
    G -->|No| H[Increment failed attempt counter]
    H --> A
    G -->|Yes| I{Account disabled? - FR-10}
    I -->|Yes| J[Block login<br/>show disabled message]
    I -->|No| K{MFA enabled? - FR-012}
    K -->|Yes| L[Prompt OTP from<br/>authenticator app]
    L --> M{OTP valid?}
    M -->|No| L
    M -->|Yes| N[Create secure session - NFR-05]
    K -->|No| N
    N --> O{User role?}
    O -->|Student| P[Redirect to Student Dashboard]
    O -->|Lecturer| Q[Redirect to Lecturer Dashboard]
    O -->|Admin| R[Redirect to Admin Dashboard]
```

### Pseudocode - login attempt handling

```text
INPUT Username, Password, OtpCode

IF Username OR Password IS INVALID THEN
    WRITE "Invalid input"
    RETURN
END IF

IF Account IS LOCKED OUT THEN
    WRITE "Too many attempts, try again later"
    RETURN
END IF

READ User RECORD WHERE Username MATCHES Username

IF User DOES NOT EXIST OR Password DOES NOT MATCH StoredHash THEN
    WRITE "Invalid credentials"
    CALL RecordFailedAttempt
    RETURN
END IF

IF User IS DISABLED THEN
    WRITE "Account disabled"
    RETURN
END IF

IF User HAS MFA ENABLED THEN
    IF OtpCode IS INVALID THEN
        WRITE "Invalid OTP"
        RETURN
    END IF
END IF

CALL CreateSecureSession WITH User
CALL ClearFailedAttempts WITH Username
OUTPUT RedirectToDashboard WITH User Role
```

## 3. Student Sign-Up & Lecturer Approval

Covers FR-13 to FR-15.

```mermaid
flowchart TD
    A[Guest opens Sign-Up view] --> B[Enter student number, first name,<br/>last name, password, course title - FR-13]
    B --> C[Create account<br/>status = pending approval]
    C --> D[Account cannot access<br/>testing system yet - FR-14]
    D --> E[Lecturer reviews pending students]
    E --> F{Lecturer approves?}
    F -->|No| G[Account stays pending/rejected]
    F -->|Yes| H[Account activated]
    H --> I[Send confirmation<br/>email/notification - FR-15]
    I --> J[Student can now log in<br/>and access tests]
```

## 4. Sign-Out Flow

Covers FR-55, FR-56.

```mermaid
flowchart TD
    A[User clicks Sign Out] --> B[Destroy/invalidate session - NFR-05]
    B --> C[Redirect to Login page]
    C --> D[Show sign-out confirmation message - FR-56]
```

## 5. Student Test-Taking Flow

Covers FR-15 to FR-25.

```mermaid
flowchart TD
    A[Student Dashboard] --> B[View pending tests - FR-15]
    A --> C[View completed tests<br/>name, date, #questions, % correct, points - FR-16/17]
    B --> D[Select a test to start]
    D --> E[Select questions for attempt<br/>see selection algorithm - FR-22/23]
    E --> F[Render testing page:<br/>test name, subject, Q number, total Qs - FR-19]
    F --> G{Time limit set? - FR-24}
    G -->|Yes| H[Show live countdown]
    G -->|No| I[No timer shown]
    H --> J{Time expires first?}
    I --> K[Student answers questions]
    J -->|Yes| L[Auto-submit test - FR-25<br/>unanswered = 0 points]
    J -->|No, student submits| M[Student submits test - FR-20]
    K --> M
    L --> N[Score test]
    M --> N[Score test - FR-21]
    N --> O[Record result against account]
    O --> P[Update completed tests list<br/>and statistics]
```

### Pseudocode - question selection (FR-22, FR-23)

```text
INPUT Student, Subject, PoolSize

SET QuestionPool TO ALL QUESTIONS FOR Subject
SET SelectedQuestions TO EMPTY LIST

IF PrioritiseWeakQuestions FEATURE IS ENABLED THEN
    SET WeakQuestions TO QUESTIONS Student FREQUENTLY GETS WRONG FROM QuestionPool
    SET SelectedQuestions TO RANDOM SUBSET OF WeakQuestions UP TO PoolSize
END IF

WHILE SIZE OF SelectedQuestions IS LESS THAN PoolSize
    SET RemainingQuestions TO QuestionPool MINUS SelectedQuestions
    ADD ONE RANDOM QUESTION FROM RemainingQuestions TO SelectedQuestions
ENDWHILE

SHUFFLE SelectedQuestions
OUTPUT SelectedQuestions
```

### Pseudocode - scoring & submission (FR-20, FR-21, FR-25)

```text
INPUT Attempt, Answers, AutoSubmitted

SET Score TO 0

FOR EACH Question IN Attempt Questions
    SET Answer TO MATCHING ENTRY IN Answers FOR Question

    IF Answer IS MISSING THEN
        SET Points TO 0
    ELSE IF Answer IS CORRECT THEN
        SET Points TO 30
    ELSE
        SET Points TO -10
    END IF

    ADD Points TO Score
END FOR

SET PercentCorrect TO CORRECT ANSWERS DIVIDED BY TOTAL QUESTIONS TIMES 100

WRITE Result RECORD WITH Student, Test, Score, PercentCorrect, CompletedAt, AutoSubmitted
OUTPUT Result
```

### Pseudocode - countdown/auto-submit timer (FR-24, FR-25)

```text
INPUT Attempt

IF Attempt Test HAS NO TIME LIMIT THEN
    RETURN
END IF

SET Deadline TO Attempt StartedAt PLUS Test TimeLimitMinutes

WHILE CURRENT TIME IS BEFORE Deadline
    SET RemainingTime TO Deadline MINUS CURRENT TIME
    OUTPUT RemainingTime TO Countdown Display
    WAIT ONE SECOND
ENDWHILE

CALL SubmitTest WITH Attempt, CurrentAnswers, AutoSubmitted SET TO TRUE
```

## 6. Student Results, Leaderboard & Export

Covers FR-26 to FR-31.

```mermaid
flowchart TD
    A[Student Dashboard] --> B[View Leaderboard<br/>top 5 per subject - FR-26/27]
    A --> C[View Stats/Results page]
    C --> D[Total points - FR-28]
    C --> E[Average score - FR-28]
    C --> F[Line chart of grades over time - FR-29]
    C --> G{Export requested? - FR-30}
    G -->|Yes| H[Generate CSV of completed tests]
    H --> I[Highlight best test by avg score - FR-31]
    H --> J[Highlight worst test by avg score - FR-31]
    G -->|No| K[Stay on results page]
```

## 7. Lecturer - Student Management

Covers the lecturer FR block (list/approve/edit/disable/delete students, progress monitoring).

```mermaid
flowchart TD
    A[Lecturer Dashboard] --> B[List all students<br/>incl. last login time]
    B --> C{Action}
    C -->|Pending account| D[Approve new student account]
    C -->|Existing student| E[Edit student data<br/>e.g. name]
    C -->|Existing student| F[Disable / Re-enable account]
    C -->|Existing student| G[Delete account]
    B --> H[Monitor student progression<br/>results, averages, progress over time]
```

## 8. Lecturer - Test & Question Management

Covers lecturer test-creation FR block.

```mermaid
flowchart TD
    A[Lecturer Dashboard] --> B[List existing tests]
    A --> C[Create new test for a subject]
    C --> D[Set optional time limit in minutes]
    A --> E[Add multiple-choice questions<br/>max 4 answers to subject pool]
    B --> F[Update existing test]
    B --> G[Delete test]
    G --> H{Any student has<br/>already attempted it?}
    H -->|Yes| I[Require confirmation before delete]
    H -->|No| J[Delete immediately]
```

## 9. Admin - Subjects & Lecturer Accounts

Covers FR-46 to FR-55.

```mermaid
flowchart TD
    A[Admin Dashboard] --> B[All lecturer capabilities<br/>FR-55]
    A --> C[Create new subject - FR-46]
    A --> D[Edit existing subject - FR-47]
    A --> E[List all subjects - FR-48]
    E --> F[No delete option — subjects<br/>are permanent for history - FR-49]
    A --> G[Create lecturer account<br/>disabled by default - FR-50]
    A --> H[Edit lecturer account - FR-51]
    A --> I[Delete lecturer account - FR-52]
    A --> J[Disable lecturer account - FR-53]
    G --> K[Activate lecturer account - FR-54]
```

## 10. Role-Based Access Control (cross-cutting)

Covers NFR (RBAC) applied to every request.

```mermaid
flowchart TD
    A[Authenticated request] --> B{Valid session? - NFR-05}
    B -->|No| C[Redirect to login]
    B -->|Yes| D{Role allowed for<br/>requested route?}
    D -->|Student route, role=Student| E[Allow]
    D -->|Lecturer route, role=Lecturer/Admin| F[Allow]
    D -->|Admin route, role=Admin| G[Allow]
    D -->|Mismatch| H[403 Forbidden /<br/>redirect to own dashboard]
```