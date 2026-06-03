# =================== BASE IMAGE VERSIONS ===================
# Keep base image tags explicit and on official Docker Hub images.
# For strict supply-chain control in CI/CD, pin these to immutable digests.
# NODE_IMAGE:    node:22-trixie-slim
# PYTHON_IMAGE:  python:3.14-slim-trixie
# POETRY:        2.1.3


# =================== BUILDER FRONTEND ===================
FROM node:22-trixie-slim AS builder_frontend

# Build frontend assets in an isolated stage.
WORKDIR /tmp/frontend

# Copy dependency manifest first so dependency install can be cached across code-only changes.
COPY frontend/package.json ./

# Install frontend dependencies.
# `npm ci` is preferred when package-lock.json exists; this project currently tracks bun.lock,
# so `npm install` is used for compatibility while keeping flags conservative.
RUN npm install --no-audit --no-fund

# Copy frontend source after dependency install to preserve cache efficiency.
COPY frontend /tmp/frontend/

# Copy only backend files required by frontend/src/pdf-icons.css @source directives.
# The relative path contract must resolve as:
#   /tmp/frontend/src/pdf-icons.css -> ../../backend/...
RUN mkdir -p /tmp/backend/applications /tmp/backend/templates
COPY backend/applications/models.py /tmp/backend/applications/
COPY backend/templates/application-pdf-template.html /tmp/backend/templates/

# Build production frontend assets, including hash-free pdf-icons.css.
RUN npm run build


# =================== BUILDER BACKEND ===================
FROM python:3.14-slim-trixie AS builder_backend

# Security-lean Python defaults.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /app

# Install only packages needed to install Poetry and Python dependencies.
# No `apt-get upgrade` here: rely on refreshed official base images for reproducibility.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Poetry version for deterministic builds.
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.3

# Copy dependency manifests first for better dependency-layer caching.
COPY backend/pyproject.toml backend/poetry.lock backend/poetry.toml /app/

# Install runtime Python dependencies into in-project .venv.
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Upgrade pip in the built virtual environment so the runtime image inherits
# the patched installer version from the copied .venv.
RUN /app/.venv/bin/python -m pip install --no-cache-dir --upgrade "pip>=26.1"


# =================== RUNTIME ===================
FROM python:3.14-slim-trixie

# Accept non-sensitive build arguments used during collectstatic.
ARG DATABASE_URL
ARG DJANGO_SECRET_KEY
ARG LOCAL_MEDIA_STORAGE
ARG PRIVATE_MEDIA_ROOT

# Runtime environment variables consumed by Django settings.
ENV DATABASE_URL=${DATABASE_URL} \
    DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY} \
    LOCAL_MEDIA_STORAGE=${LOCAL_MEDIA_STORAGE} \
    PRIVATE_MEDIA_ROOT=${PRIVATE_MEDIA_ROOT}

# Runtime Python defaults.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app \
    TZ=Australia/Perth

# Install only minimal runtime tools.
# - wget: required by container HEALTHCHECK
# - tzdata/ca-certificates: timezone + TLS trust
RUN apt-get update \
    && apt-get install --no-install-recommends -y wget tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Install Prince XML in a dedicated layer so PDF runtime dependency management
# is isolated from the base runtime package installation.
RUN apt-get update \
    && apt-get install --no-install-recommends -y gdebi-core \
    && DEB_FILE=prince_16.2-1.deb \
    && ARCH="$(dpkg --print-architecture)" \
    && if [ "$ARCH" = "arm64" ]; then \
    PRINCE_URL="https://www.princexml.com/download/prince_16.2-1_debian13_arm64.deb"; \
    elif [ "$ARCH" = "amd64" ]; then \
    PRINCE_URL="https://www.princexml.com/download/prince_16.2-1_debian13_amd64.deb"; \
    else \
    echo "Unsupported architecture for Prince package: $ARCH"; \
    exit 1; \
    fi \
    && wget -O "${DEB_FILE}" "${PRINCE_URL}" \
    && gdebi --non-interactive "${DEB_FILE}" \
    && rm -f "${DEB_FILE}" \
    && prince --version \
    && apt-get purge -y --auto-remove gdebi-core \
    && rm -rf /var/lib/apt/lists/*

# Create least-privilege runtime user and app directory.
RUN groupadd -g 5000 appuser \
    && useradd --gid 5000 --uid 5000 --create-home --home-dir /home/appuser --no-log-init appuser \
    && mkdir /app \
    && chown -R appuser:appuser /app

WORKDIR /app

# Copy backend source code and built frontend assets.
COPY --chown=appuser:appuser backend /app/
COPY --from=builder_frontend --chown=appuser:appuser /tmp/frontend/dist /app/assets

# Copy the prepared virtual environment from backend builder stage.
COPY --from=builder_backend --chown=appuser:appuser /app/.venv /app/.venv

# Drop privileges before running Django management commands and app process.
USER appuser

# Collect static at build time so runtime start is faster and deterministic.
RUN python manage.py collectstatic --noinput

# Expose Django/gunicorn port.
EXPOSE 8080

# Basic HTTP healthcheck endpoint.
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]

# Launch gunicorn via project entrypoint.
ENTRYPOINT ["/app/entrypoint.sh"]
