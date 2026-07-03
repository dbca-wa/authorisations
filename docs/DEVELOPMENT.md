# Development Guide

This document covers setup, installation, and running the application locally for development.

## Prerequisites

- Docker engine: https://docs.docker.com/engine/install/
- Python 3 (recommended version 3.14 via pyenv)
- Poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
- Bun (recommended instead of npm): https://bun.com/docs/installation

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
python -c 'import secrets; print(secrets.token_hex(25))'
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

Navigate to the frontend directory and install dependencies with Bun:

```bash
cd ../frontend
bun install
```

## Run the application

### Backend

Run the Django development server (within the `backend` directory):

```bash
poetry run python manage.py runserver
```

### Frontend

In another terminal window, navigate to the `frontend` directory and run the Bun development server:

```bash
bun run dev
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

Backend pytest uses a dedicated Django settings module at `config.test_settings`, backed by SQLite, so you do not need PostgreSQL `CREATEDB` privileges just to run the automated suite locally.

### Backend tests

Run the fast backend suite:

```bash
cd ../backend
poetry run pytest
```

Run backend tests in parallel with coverage:

```bash
poetry run pytest -n auto --cov --cov-report=term-missing --cov-report=html --cov-report=xml
```

### Frontend tests

Run the frontend test suite:

```bash
cd ../frontend
bun run test
```

Run frontend tests with coverage:

```bash
bun run test:coverage
```

### End-to-end tests

Run the E2E browser suite:

```bash
cd ../backend
poetry run pytest e2e/tests -v
```

### For more information

For full testing architecture, best practices, CI behaviour, E2E guidance, and troubleshooting, refer to [TESTING.md](TESTING.md).

## Backend management commands

Common Django management commands used in development:

- `poetry run python manage.py runserver` — Run dev server
- `poetry run python manage.py test` — Run tests
- `poetry run python manage.py migrate` — Apply migrations
- `poetry run python manage.py collectstatic` — Collect static files
- `poetry run python manage.py normalise_questionnaire_sort_order` — Rebuild questionnaire sort order globally
  - Dry-run mode: `poetry run python manage.py normalise_questionnaire_sort_order --dry-run`

## Frontend commands

See [FRONTEND-CONVENTIONS.md](FRONTEND-CONVENTIONS.md) for frontend development commands and package manager policy.

---

**See [README.md](README.md) for the documentation index.**
