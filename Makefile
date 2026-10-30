## setup-db: Create the PostgreSQL schema.
.PHONY: setup-db
setup-db:
	python3 -m database.migrations.migrate

## db-shell: Open the PostgreSQL shell.
.PHONY: db-shell
db-shell:
	set -a; [ -f .env ] && . ./.env; set +a; \
	PGPASSWORD="$$PASSWORD" psql -h "$${DATABASE_URL:-localhost}" -p "$${DATABASE_PORT:-5432}" -U "$${USERNAME:-postgres}" "$${DATABASE_NAME:-reinforcement_testing}"

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
