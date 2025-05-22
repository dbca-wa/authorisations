# =================== BUILD FRONTEND ===================
FROM ubuntu:24.04 AS builder_frontend

# # Install system upgrades & dependencies
# RUN apt-get clean
# RUN apt-get update
# RUN apt-get upgrade -y
# RUN apt-get install --no-install-recommends -y curl ca-certificates coreutils
# RUN update-ca-certificates

# # Install Node.js
# # https://github.com/nodesource/distributions/
# RUN curl -fsSL https://deb.nodesource.com/setup_23.x -o nodesource_setup.sh
# RUN bash nodesource_setup.sh
# RUN apt-get install --no-install-recommends -y nodejs

# # Copy frontend project
# COPY frontend /tmp/frontend

# # Install frontend dependencies & build assets
# RUN cd /tmp/frontend; npm install; npm run build


# # =================== BUILD BACKEND ===================
# FROM builder_frontend AS builder_backend

# # # Environment setup
# ENV DEBIAN_FRONTEND=noninteractive
# ENV TZ="Australia/Perth"

# # Install system upgrades & dependencies
# RUN apt-get clean
# RUN apt-get update
# RUN apt-get upgrade -y
# RUN apt-get install --no-install-recommends -y curl wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata rsyslog gunicorn virtualenv
# RUN apt-get install --no-install-recommends -y libpq-dev patch libreoffice
# RUN apt-get install --no-install-recommends -y postgresql-client mtr htop vim nano npm sudo
# RUN apt-get install --no-install-recommends -y bzip2 unzip
# RUN apt-get install --no-install-recommends -y graphviz libgraphviz-dev pkg-config
# RUN ln -s /usr/bin/python3 /usr/bin/python 
# RUN apt remove -y libnode-dev
# RUN apt remove -y libnode72
# RUN update-ca-certificates

# # Update timezone
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# # Install Poetry
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
# ENV PATH="${PATH}:/etc/poetry/bin"

# WORKDIR /app

# # Copy backend project files into container
# COPY backend /app

# # Copy the frontend generated assets
# COPY --from=builder_frontend /tmp/frontend/dist /app/assets

# # Install virtualenv & dependencies (within the project folder)
# RUN poetry config virtualenvs.in-project true
# RUN poetry install --no-root --no-interaction --no-ansi

# # Collect static (inside the virtualenv)
# RUN poetry run python manage.py collectstatic --noinput

# # DBCA default Scripts
# RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
# RUN chmod 755 /tmp/default_script_installer.sh
# RUN /tmp/default_script_installer.sh


# # =================== RUNTIME ===================
# FROM builder_backend

# # Create a non-root user to run the app
# RUN groupadd -g 5000 appuser
# RUN useradd --gid 5000 --uid 5000 --create-home --home-dir /home/appuser --no-log-init appuser
# RUN echo 'alias ls="ls -lah --color=auto"' >> /home/appuser/.bash_aliases

# # Give the ownership for project directory
# RUN chown -R appuser:appuser /app

# # Switch to non-root user
# USER appuser

# # Use the virtualenv python always
# ENV PATH="/app/.venv/bin:${PATH}"
# ENV PYTHONPATH=/app

# # Expose django app on port 8080
# EXPOSE 8080

# HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]

# # Launch gunicorn
# ENTRYPOINT ["/app/entrypoint.sh"]
# # ENTRYPOINT ["sleep", "infinity"]
