#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/blue-shark-labs"
SOURCE_DIR="${APP_DIR}/source"
COMPOSE_FILE="${SOURCE_DIR}/docker-compose.yml"
ENV_FILE="${APP_DIR}/production.env"
SERVICE="app"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} is missing." >&2
  exit 1
fi
if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "ERROR: ${COMPOSE_FILE} is missing." >&2
  exit 1
fi
if [[ -z "${GITHUB_SHA:-}" ]]; then
  echo "ERROR: GITHUB_SHA is required." >&2
  exit 1
fi

export IMAGE_TAG="${GITHUB_SHA}"

compose() {
  docker compose --project-directory "${SOURCE_DIR}" -f "${COMPOSE_FILE}" "$@"
}

if ! docker network inspect web >/dev/null 2>&1; then
  docker network create web
fi

echo "Validating Compose configuration..."
compose config --quiet

OLD_CONTAINER="$(compose ps -q "${SERVICE}" || true)"
OLD_IMAGE_ID=""
if [[ -n "${OLD_CONTAINER}" ]]; then
  OLD_IMAGE_ID="$(docker inspect --format '{{.Image}}' "${OLD_CONTAINER}")"
  docker image tag "${OLD_IMAGE_ID}" blue-shark-labs:rollback
  echo "Saved previous image as blue-shark-labs:rollback"
fi

echo "Building blue-shark-labs:${IMAGE_TAG}..."
if ! compose build "${SERVICE}"; then
  echo "ERROR: Image build failed; existing container was not replaced." >&2
  exit 1
fi

echo "Starting new application..."
if ! compose up -d --no-deps "${SERVICE}"; then
  echo "ERROR: Compose failed to start the new version." >&2
  if [[ -n "${OLD_IMAGE_ID}" ]]; then
    export IMAGE_TAG=rollback
    compose up -d --no-build --no-deps "${SERVICE}" || true
  fi
  exit 1
fi

# Wait for Docker's HTTP health check to report healthy (up to 120 seconds).
deadline=$((SECONDS + 120))
while (( SECONDS < deadline )); do
  CONTAINER="$(compose ps -q "${SERVICE}" || true)"
  if [[ -n "${CONTAINER}" ]]; then
    STATE="$(docker inspect --format '{{.State.Status}}' "${CONTAINER}" 2>/dev/null || true)"
    HEALTH="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${CONTAINER}" 2>/dev/null || true)"

    if [[ "${STATE}" == "running" && "${HEALTH}" == "healthy" ]]; then
      echo "Deployment healthy: ${IMAGE_TAG}"
      compose ps
      exit 0
    fi

    if [[ "${STATE}" == "exited" || "${STATE}" == "dead" ]]; then
      break
    fi
  fi
  sleep 3
done

echo "ERROR: New version did not become healthy." >&2
compose logs --tail=100 "${SERVICE}" || true

if [[ -n "${OLD_IMAGE_ID}" ]]; then
  echo "Attempting rollback to previous image..." >&2
  export IMAGE_TAG=rollback
  if compose up -d --no-build --no-deps "${SERVICE}"; then
    echo "Rollback command issued. Verify health and logs." >&2
  else
    echo "ERROR: Automatic rollback failed; manual intervention required." >&2
  fi
fi

exit 1
