# UCW Reinforcement Testing Platform
---

## 1. Tech stack

- Languages
- Core frameworks 
- Docker or other containerisation (has to be deployed)

## 2. Architecture

- Clean architecture — dependencies point inward: `rest` → `usecase` → `database`, with `domain` entities shared across all layers.
  - **rest/** — HTTP delivery only: Flask routes/handlers translate requests into usecase calls and render responses. No SQL, no business rules.
  - **usecase/** — business logic/orchestration: coordinates one or more database calls and enforces business rules (e.g. auth attempts, scoring, question selection). No Flask/HTTP objects, no SQL.
  - **database/** — persistence only: raw SQL queries and row-mapping helpers. The only code that talks to Postgres.
  - **domain/entities/** — plain data objects (dataclasses) passed between layers; no behavior/logic.

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

Clean architecture — dependencies point inward (REST → use cases → database):

```text
├── app.py                       # entry point
├── conftest.py                  # puts project root on sys.path for tests
├── Makefile                     # setup-db, db-shell, run, test
├── rest/                        # REST layer
│   ├── router.py                # Set up API routes
│   ├── home.py                  # home_route()
│   ├── helpers/rest_helpers.py  # shared JSON helpers
│   └── *_test.py                # co-located tests
├── usecase/                     # use case layer: business logic, no Flask/SQL
├── database/                    # database layer
│   ├── connection.py            # PostgresConnectionProvider (raw psycopg)
│   ├── helpers/                 # row-mapping helpers
│   └── migrations/migrate.py    # schema setup (make setup-db)
├── domain/entities/             # plain data objects shared across layers
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
make seed-student-dashboard   # add repeatable student dashboard sample data
make seed-dev-data            # import data/users.json and data/subjects.json
make install-frontend         # download the standalone Tailwind CLI binary (via pytailwindcss, no Node.js)
make build-css                # compile static/css/styles.css (or `make watch-css` while developing)
make run                      # or: python3 app.py
make test                     # or: pytest -v
```

`setup-db` and `seed-dev-data` read database settings from `dev.env` (or from
environment variables already set in the shell). Before seeding, set
`DEV_SEED_PASSWORD` to a local-only password; placeholder password hashes in
`data/users.json` are replaced with hashes for that password. For PowerShell:

```powershell
$env:DEV_SEED_PASSWORD = "your-local-development-password"
python -m database.migrations.migrate
python -m database.migrations.seed_dev_data
Remove-Item Env:DEV_SEED_PASSWORD
```

The importer maps the numeric JSON user IDs to stable database UUIDs and stores
subject/lecturer links in `subject_lecturers`. Subject `code` and `updatedAt`
fields are not imported because they are not columns in the current schema.
Lecturer references absent from `users.json` are reported and skipped.

Requires a running PostgreSQL instance matching the settings in `dev.env`.
Use `DATABASE_USER` for the database account name; avoid `USERNAME`, which is
predefined by Windows and may override the value loaded from an env file.

---
