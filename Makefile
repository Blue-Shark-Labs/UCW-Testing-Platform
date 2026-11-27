## setup-db: Create the PostgreSQL schema.
.PHONY: setup-db
setup-db:
	python3 -m database.migrations.migrate

## seed-student-dashboard: Add sample tests and student attempts from database/migrations/seed_data (run after seed-dev-users).
.PHONY: seed-student-dashboard
seed-student-dashboard:
	python3 -m database.migrations.seed_student_dashboard
## seed-dev-users: Seed dev logins and sample students from database/migrations/seed_data/users.json (dev/nonprod only).
.PHONY: seed-dev-users
seed-dev-users:
	python3 -m database.migrations.seed_dev_users

## submit-expired-attempts: Score timed-out attempts (schedule via cron).
.PHONY: submit-expired-attempts
submit-expired-attempts:
	python3 -m scripts.submit_expired_attempts
## migrate-dev-db: Migrate all development data.
.PHONY: migrate-dev-db
migrate-dev-db:
	@$(MAKE) setup-db seed-dev-users seed-student-dashboard
## clear-dev-db: Delete all data from the dev database, keeping the schema (asks for confirmation; refuses prod).
.PHONY: clear-dev-db
clear-dev-db:
	python3 -m database.migrations.clear_dev_db

## db-shell: Open the PostgreSQL shell.
.PHONY: db-shell
db-shell:
	set -a; [ -f .env ] && . ./.env; set +a; \
	PGPASSWORD="$$PASSWORD" psql -h "$${DATABASE_URL:-localhost}" -p "$${DATABASE_PORT:-5432}" -U "$${DATABASE_USER:-$${USERNAME:-postgres}}" "$${DATABASE_NAME:-reinforcement_testing}"

# Pinned to v3: matches the tailwind.config.js/@tailwind directive setup used here.
export TAILWINDCSS_VERSION ?= v3.4.13

## install-frontend: Download the standalone Tailwind CLI binary (no Node.js needed).
.PHONY: install-frontend
install-frontend:
	tailwindcss_install

## build-css: Compile and minify the Tailwind stylesheet for production.
.PHONY: build-css
build-css:
	tailwindcss -i ./static/css/src/input.css -o ./static/css/styles.css --minify

## run: Run the app in development mode.
.PHONY: run
run:
	python3 app.py

## test: Run all tests.
.PHONY: test
test:
	pytest -v

## install-e2e: Download the Chromium browser used by the browser tests.
.PHONY: install-e2e
install-e2e:
	playwright install chromium

## test-e2e: Run the Playwright browser tests (add --headed to watch).
.PHONY: test-e2e
test-e2e:
	pytest -v e2e
