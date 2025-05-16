# ====================== BUILD FRONTEND ======================
FROM oven/bun:1.2.13-slim AS builder_frontend

# Copy the entire frontend folder
WORKDIR /client
COPY frontend /client/

# Install dependencies, including devDependencies needed for the build process (no --omit=dev)
# RUN npm install
RUN bun add -d esbuild@0.25.2
RUN bun install

# This command runs the "npm build" script inside the container (it will use above env variables).
# RUN npm run build 
RUN bun run build 


# ====================== BUILD BACKEND ======================
FROM python:3.13.3 AS builder_backend

# Environment setup
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ="Australia/Perth"
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install --no-install-recommends -y curl wget gcc tzdata

# Install Poetry
RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
ENV PATH="${PATH}:/etc/poetry/bin"

# Create a non-root user to run the app
ARG UID=10001
ARG GID=10001
RUN groupadd -g "${GID}" appuser \
    && useradd --create-home --home-dir /home/appuser --no-log-init --uid "${UID}" --gid "${GID}" appuser

# Set working directory
WORKDIR /app

# Move local files to container
COPY backend/. /app

# Copy the frontend production build here
COPY --from=builder_frontend /client/dist/ /app/staticfiles/

# /app folder ownership
RUN chown -R ${UID}:${GID} /app

# Switch to non-root user
USER appuser

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root


# ENTRYPOINT ["python", "sleep.py"]

# Collect static
RUN python manage.py collectstatic --noinput

# Expose django app on port 8080
EXPOSE 8080

HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]

# Launch gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]