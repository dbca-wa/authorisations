# Development Guide

This document covers setup, installation, and running the application locally for development.

## Prerequisites

- Docker engine: https://docs.docker.com/engine/install/
- Python 3 (recommended version 3.14 via pyenv)
- Poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
- Node.js 22 and npm: https://nodejs.org/

## Create the database

This application runs on PostgreSQL. The easiest way to run a PostgreSQL instance is via a Docker image.

Pull the latest PostgreSQL image:

```bash
docker pull postgres
```

Create a Docker volume to persist the database:

```bash
docker volume create pgdata
```

Run the PostgreSQL container (set the `postgres` user password, mount the persistent data volume and expose the port):

```bash
docker run -d --name psql -e POSTGRES_PASSWORD=mysecretpassword -v pgdata:/var/lib/postgresql -p 5432:5432 postgres
```

Check the container is running:

```bash
docker ps
```

Next time you can start the container with:

```bash
docker start psql
```

Once the database is up and running, create the application database and user. Ideally there should be a dedicated database user (not the `postgres` superuser) and the database owner should be that user. This can be achieved by pgAdmin, `psql` command line tool or any other PostgreSQL client.

## Get the source code

```bash
cd ~/dev # or wherever
git clone git@github.com:dbca-wa/authorisations.git
```

## Setup the backend

Navigate to the backend directory and create a `.env` file from the template:

```bash
cd authorisations/backend
cp .env.template .env
```

Edit the `.env` file and set the environment variables, including:
- The database connection string with your newly created database and user
- The full path for your local `PRIVATE_MEDIA_ROOT`

Generate a Django secret key and add it to your `.env` file:

```bash
cd backend && poetry run python -c 'import secrets; print(secrets.token_hex(25))'
```

Install Python dependencies via Poetry (run within the `backend` directory):

```bash
poetry install
```

Poetry automatically creates a virtual environment within the same directory, which is git ignored.

Apply the database migrations:

```bash
poetry run python manage.py migrate
```

Create a superuser to access the admin interface on development environment:

```bash
poetry run python manage.py createsuperuser
```

### Activate the virtual environment

```bash
source ~/dev/authorisations/backend/.venv/bin/activate
```

It is often practical to assign an alias to the above command in your `.bash_aliases` file:

```bash
alias activate='source ~/dev/authorisations/backend/.venv/bin/activate'
```

## Setup the frontend

Navigate to the frontend directory and install dependencies with npm:

```bash
cd ../frontend
npm install
```

## Run the application

### Backend

Run the Django development server (within the `backend` directory):

```bash
poetry run python manage.py runserver
```

### Frontend

In another terminal window, navigate to the `frontend` directory and run the npm development server:

```bash
npm run dev
```

The application should be accessible in your web browser at `http://localhost:8000` and the Django admin interface at `http://localhost:8000/admin`. The backend proxies the frontend Vite server and reloads the page when any changes are made.

### Notes

- You can ignore the "STATICFILES_DIRS setting does not exist" warning when running the Django development server. It is needed only when running in the production environment.
- If the warning bothers you, create an empty `assets` directory in the `backend` folder (also git ignored):

```bash
cd ../backend
mkdir assets
```

## Run the test suites

**For comprehensive testing guidelines, test commands, and architecture, refer to [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md#test-coverage).**

Quick start:
- Backend: `cd backend && poetry run pytest`
- Frontend: `cd frontend && npm run test:coverage`
- E2E: `cd backend && poetry run pytest e2e/tests -v`

## Backend management commands

Common Django management commands used in development:

- `poetry run python manage.py runserver` — Run dev server
- `poetry run python manage.py migrate` — Apply migrations
- `poetry run python manage.py collectstatic` — Collect static files
- `poetry run python manage.py normalise_questionnaire_sort_order` — Rebuild questionnaire sort order globally
  - Dry-run mode: `poetry run python manage.py normalise_questionnaire_sort_order --dry-run`

**For full testing commands, refer to [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md#test-coverage).**

## Static files

Static files in this project are managed using a hybrid approach between Vite and Django:

1. **Frontend-driven assets**: Any assets placed in `frontend/public/` (for example `favicon.svg`) are automatically copied to `frontend/dist/` during the `npm run build` step.
2. **Django-driven assets (Production/UAT)**: In the Docker image, built assets are copied from the builder stage into `backend/assets/`. Django's base `STATICFILES_DIRS` includes this folder, allowing `collectstatic` to gather them into `STATIC_ROOT`.
3. **Reference in templates**: To reference these files in Django templates (like `vite.html`), use the `{% static 'path/to/file' %}` tag (ensure `{% load static %}` is present). In Production, this resolves to hashed filenames for cache busting.
4. **Development flow**: In local development, you generally use the Vite dev server (`npm run dev`). However, if you build the frontend locally, Django will automatically detect the `frontend/dist/` directory and add it to `STATICFILES_DIRS`, allowing you to test production-like static serving without moving files.

## Frontend commands

See [FRONTEND-CONVENTIONS.md](FRONTEND-CONVENTIONS.md) for frontend development commands and package manager policy.

---

**See [README.md](README.md) for the documentation index.**
