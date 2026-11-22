# UCW Reinforcement Testing Platform
---

## 1. Tech stack

- Languages
- Core frameworks 
- Docker or other containerisation (has to be deployed)

## 2. Architecture

- Layered architecture — dependencies point inward: `rest` → `database`.
  - **rest/** — Flask routes/handlers plus request-level business rules (e.g. login lockout, registration validation, scoring). No SQL.
  - **database/** — persistence only: raw SQL queries, row mapping and the dataclasses they return. The only code that talks to Postgres.

## 3. Database & data

- Postgresql

## 4. Testing

- Test frameworks 
- Coverage

## 5. Ways of working (Git)

- Branch naming convention `*/*`
- Reviewers required, no self-merge.
- CI checks on each push.

## 6. Repo structure

Layered architecture — dependencies point inward (REST → database):

```text
├── app.py                       # entry point
├── conftest.py                  # puts project root on sys.path for tests
├── Makefile                     # setup-db, db-shell, run, test
├── rest/                        # REST layer
│   ├── router.py                # Set up API routes
│   ├── home.py                  # home_route()
│   ├── helpers/rest_helpers.py  # shared JSON helpers
│   └── *_test.py                # co-located tests
├── database/                    # database layer
│   ├── connection.py            # PostgresConnectionProvider (raw psycopg)
│   ├── helpers/                 # shared query helpers
│   └── migrations/migrate.py    # schema setup (make setup-db)
├── templates/                   # templates + partials
├── static/css/                  # styles
├── requirements.txt
└── .env.example
```

---

## Dev Instructions

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp dev-env-template dev.env   # set DATABASE_URL, DATABASE_NAME, DATABASE_USER and PASSWORD
make setup-db                 # create the PostgreSQL schema
make seed-dev-users           # add dev logins and sample students
make seed-student-dashboard   # add sample subjects, tests, questions and student attempts
make install-frontend         # download the standalone Tailwind CLI binary (via pytailwindcss, no Node.js)
make build-css                # compile static/css/styles.css (or `make watch-css` while developing)
make run                      # or: python3 app.py
make test                     # or: pytest -v
```

`make migrate-dev-db` runs `setup-db`, `seed-dev-users` and
`seed-student-dashboard` in order. To start from a clean slate, run
`make clear-dev-db` first; it empties every table but keeps the schema.
The sample data lives in
`database/migrations/seed_data/`: `users.json` (accounts; students without a
`password` use `defaultPassword`), `subjects.json` (with `lecturerEmails`), `tests.json`,
`questions.json` and `test_activity.json`. In `test_activity.json` each
completed test only records how many answers were `correct`; the seeder derives
the score, points and per-question answers from that.

The make targets read database settings from `dev.env` (or from environment
variables already set in the shell).

Requires a running PostgreSQL instance matching the settings in `dev.env`.
Use `DATABASE_USER` for the database account name; avoid `USERNAME`, which is
predefined by Windows and may override the value loaded from an env file.

---
