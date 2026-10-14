# UCW Reinforcement Testing Platform
---

## 1. Tech stack

- Languages
- Core frameworks 
- Docker or other containerisation (has to be deployed)

## 2. Architecture

- Clean architecture

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
├── database/                    # database layer
│   ├── connection.py            # PostgresConnectionProvider (raw psycopg)
│   ├── helpers/                 # row-mapping helpers
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
cp .env.example .env          # then edit DATABASE_URL if needed
make setup-db                 # create the PostgreSQL schema
make install-frontend         # download the standalone Tailwind CLI binary (via pytailwindcss, no Node.js)
make build-css                # compile static/css/styles.css (or `make watch-css` while developing)
make run                      # or: python3 app.py
make test                     # or: pytest -v
```

Requires a running PostgreSQL instance matching `DATABASE_URL`.

---
