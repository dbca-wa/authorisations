# Installation

This is a guide to install the application on a local machine for development purposes.

## Pre-requesites
- Docker engine : https://docs.docker.com/engine/install/
- Python 3 (recommended version 3.14 via pyenv)
- Poetry : https://python-poetry.org/docs/#installing-with-the-official-installer
- Bun (recommended instead of npm) : https://bun.com/docs/installation


## Create the database
This application runs on PostgreSQL. Easiest way to run a postgresql instance is via docker image.

Pull the latest postgres image:
> docker pull postgres

Create a docker volume to persist the database:
> docker volume create pgdata

Run the PostgreSQL container (set the `postgres` user password, mount the persistent data volume and expose the port):
> docker run -d --name psql -e POSTGRES_PASSWORD=mysecretpassword -v pgdata:/var/lib/postgresql/data -p 5432:5432 postgres

Check the container is running:
> docker ps

Next time you can start the container with:
> docker start psql

Once the database up and running, create the application database and user. Ideally there should be a dedicated database user (not the `postgres` superuser) and the database owner should be that user. This can be achieved by pgAdmin, `psql` command line tool or any other PostgreSQL client.


## Codebase

Get the source code from repository:
> cd ~/dev # or wherever \
> git clone git@github.com:dbca-wa/authorisations.git

### Setup the backend
Create your own copy of the `.env` file and set the environment variables, including the database connection string with your newly created database and user.
> cd authorisations/backend \
> cp .env.template .env

Create a Django secret key and set it in your `.env` file as well.
> python -c 'import secrets; print(secrets.token_hex(25))'

Install the Python dependencies via Poetry (run within the `backend` directory):
> poetry install

Virtual environment should be automatically created by Poetry within the same directory, which is git ignored. 

Apply the database migrations:
> ./manage.py migrate

Create a superuser to access the admin interface on developement environment:
> ./manage.py createsuperuser

### Setup the frontend

Navigate to the `frontend` directory and install the dependencies with Bun:
> cd ../frontend \
> bun install

## Run the application
Activate the virtual environment:
> source ~/dev/authorisations/backend/.venv/bin/activate

It is often practical to assign an alias to the above command in your `.bash_aliases` file, e.g. :
> alias activate='source ~/dev/authorisations/backend/.venv/bin/activate'

Run the Django development server (within the `backend` directory):
> ./manage.py runserver

In another terminal window, navigate to the `frontend` directory and run the Bun development server:
> bun run dev

## Notes
You can ignore the _"STATICFILES_DIRS setting does not exist"_ warning when running the Django development server. It is needed only when running in the production environment. If it bothers you, you can create an empty directory, which is also git ignored.

> cd ../backend \
> mkdir assets


You should be able to access the application in your web browser at `http://localhost:8000` and the Django admin interface at `http://localhost:8000/admin`. The backend proxies the frontend vite.js server and reloads the page when any changes are made.