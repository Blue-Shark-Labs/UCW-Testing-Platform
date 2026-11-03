
# syntax=docker/dockerfile:1

# --------------------------------------------------
# Stage 1: Build Tailwind CSS
# --------------------------------------------------
FROM debian:bookworm-slim AS tailwind-builder

ARG TARGETARCH
ARG TAILWINDCSS_VERSION=v3.4.13

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) TAILWIND_BINARY="tailwindcss-linux-x64" ;; \
      arm64) TAILWIND_BINARY="tailwindcss-linux-arm64" ;; \
      *) echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fsSL \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWINDCSS_VERSION}/${TAILWIND_BINARY}" \
      -o /usr/local/bin/tailwindcss; \
    chmod +x /usr/local/bin/tailwindcss

WORKDIR /src

COPY tailwind.config.js ./
COPY templates ./templates
COPY static/css/src/input.css ./static/css/src/input.css

RUN tailwindcss \
    -c ./tailwind.config.js \
    -i ./static/css/src/input.css \
    -o ./static/css/styles.css \
    --minify \
    && test -s ./static/css/styles.css


# --------------------------------------------------
# Stage 2: Install Python dependencies
# --------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir gunicorn


# --------------------------------------------------
# Stage 3: Production runtime
# --------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY app.py requirements.txt ./
COPY database ./database
COPY domain ./domain
COPY rest ./rest
COPY templates ./templates
COPY static ./static

# Replace/add the generated production Tailwind stylesheet.
COPY --from=tailwind-builder \
    /src/static/css/styles.css \
    ./static/css/styles.css

# Fail the image build if the production stylesheet is missing.
RUN test -s /app/static/css/styles.css

# Run as a non-root user.
RUN useradd --system --uid 10001 --user-group --create-home appuser \
    && chown -R appuser:appuser /app

USER 10001:10001

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]