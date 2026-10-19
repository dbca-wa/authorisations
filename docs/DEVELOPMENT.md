# Development Guide

This document covers setup, installation, and running the application locally for development.

## Prerequisites

- Docker engine: https://docs.docker.com/engine/install/
- Python 3 (recommended version 3.14 via pyenv)
- Poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
- Node.js 26 and npm 11.x: https://nodejs.org/
  - **npm Version Alignment:** Local development must use npm 11.x. The Docker base image (`node:22-trixie-slim`) includes npm 10.9.9, which the Dockerfile automatically upgrades to npm 11.x to ensure lock file compatibility. If you encounter `npm ci` failures in Docker builds after transitive dependency upgrades, verify your local npm version matches the Dockerfile upgrade target using `npm --version`.

## Get the source code

```bash
cd ~/dev # or wherever
git clone git@github.com:dbca-wa/authorisations.git
cd authorisations
```

## Local environment (secrets) file

Navigate to the backend directory and create a `.env` file from the template:

```bash
cd backend
cp .env.template .env
```

Edit the `.env` file and set the required environment variables. Generate secure random values for:
- `DJANGO_SECRET_KEY` — Use: `python -c 'import secrets; print(secrets.token_hex(25))'`
- `POSTGRES_PASSWORD` — PostgreSQL superuser password
- `DATABASE_PASSWORD` — Application database user password (use the same command above)

**Important**: When you set `DATABASE_PASSWORD`, you must also duplicate that same value in the `DATABASE_URL` line:

```env
DATABASE_PASSWORD=your_generated_password_here
DATABASE_URL=postgresql://authorisations_dev:your_generated_password_here@localhost:5432/authorisations_dev
```

The password appears in both places - `DATABASE_PASSWORD` is used by the database initialization script, and `DATABASE_URL` is used by Django to connect.

Also set:
- `PRIVATE_MEDIA_ROOT` — Full path to your local media directory (replace `[user]` with your username)

## Database

This application runs on PostgreSQL 17 via Docker Compose.

### Initial setup (first time only)

Start the PostgreSQL container:

```bash
cd backend
docker compose --env-file .env -f postgresql.yml up -d
```

This creates:
- Container: `authorisations_psql`
- Database: `authorisations_dev`
- Application user: `authorisations_dev`
- Volume: `authorisations_postgres_data`

### Starting and stopping the database

Start the existing container:

```bash
docker start authorisations_psql
```

Stop the container:

```bash
docker stop authorisations_psql
```

View logs:

```bash
docker logs authorisations_psql
```

### Restoring a backup

When setting up for the first time, you may need to restore a database backup from UAT.

If you have a `.sql` backup file, restore it using:

```bash
cat ./path/to/backup.sql | docker exec -i authorisations_psql pg_restore --verbose --no-privileges --no-owner -U authorisations_dev -d authorisations_dev
```

The `--no-privileges` and `--no-owner` flags skip role and ownership restoration, which prevents errors when the backup contains users or roles that don't exist in your environment.

## Setup backend

Navigate to the backend directory and install Python dependencies via Poetry:

```bash
cd backend
poetry install
```

Poetry automatically creates a virtual environment within the same directory, which is git ignored.

Run database migrations (if starting with a fresh database, or to ensure you have the latest schema):

```bash
poetry run python manage.py migrate
```

Create or designate a superuser to access the admin interface. You can use either method:

**Method 1: Interactive prompt** (if you are starting with an empty database)

```bash
poetry run python manage.py createsuperuser
```

**Method 2: Set password on existing user** (if you already have a user account from the backup)

```bash
poetry run python manage.py shell
```

Then in the Python shell, run:

```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='your_username')
user.set_password('your_new_password')
user.is_staff = True
user.is_superuser = True
user.save()
exit()
```

Replace `your_username` and `your_new_password` with your actual values.

## Setup frontend

Navigate to the frontend directory and install dependencies with npm:

```bash
cd ../frontend
npm install
```

## Virtual environment

### Activate the virtual environment

```bash
source ~/dev/authorisations/backend/.venv/bin/activate
```

It is practical to assign an alias to activate the virtual environment in your `.bash_aliases` or `.bashrc` file:

```bash
alias activate='source ~/dev/authorisations/backend/.venv/bin/activate'
```

Then you can simply run:

```bash
activate
```

## Development server

### Starting the database and environment

Start the PostgreSQL container:

```bash
docker start authorisations_psql
```

Activate the virtual environment:

```bash
activate
```

### Running the backend

In one terminal, start the Django development server:

```bash
cd backend
poetry run python manage.py runserver
```

### Running the frontend

In another terminal, start the frontend development server:

```bash
cd frontend
npm run dev
```

The application should be accessible in your web browser at `http://localhost:8000` and the Django admin interface at `http://localhost:8000/admin`. The backend proxies the frontend Vite server and reloads the page when any changes are made.

### Notes

- You can ignore the "STATICFILES_DIRS setting does not exist" warning when running the Django development server. It is needed only when running in the production environment.
- If the warning bothers you, create an empty `assets` directory in the `backend` folder (also git ignored):

```bash
cd backend
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

- `cd backend && poetry run python manage.py runserver` — Run dev server
- `cd backend && poetry run python manage.py migrate` — Apply migrations
- `cd backend && poetry run python manage.py collectstatic` — Collect static files
- `cd backend && poetry run python manage.py normalise_questionnaire_sort_order` — Rebuild questionnaire sort order globally
  - Dry-run mode: `cd backend && poetry run python manage.py normalise_questionnaire_sort_order --dry-run`

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
