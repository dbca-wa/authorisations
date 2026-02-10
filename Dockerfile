# =================== BUILDER BASE ===================
FROM ubuntu:24.04 AS builder_base

## Environment setup
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Australia/Perth

## Install system upgrades & dependencies
RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y

# Add deadsnakes repo for newer python versions
RUN apt install --no-install-recommends --fix-missing -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa

# Install with single comment and let apt-get to solve the dependencies.
RUN apt-get install --no-install-recommends --fix-missing -y \
    # command-line tools
    curl wget git htop vim nano sudo mtr coreutils rsyslog \
    # libraries
    tzdata libmagic-dev gcc binutils libproj-dev gdal-bin \
    bzip2 unzip libpq-dev patch pkg-config ca-certificates \
    # python-psql
    python3.13-full python3.13-dev postgresql-client

RUN apt remove -y libnode-dev
RUN apt remove -y libnode72
RUN update-ca-certificates

# Update timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

## FRONTEND
# Install Node.js
# https://github.com/nodesource/distributions/
RUN curl -fsSL https://deb.nodesource.com/setup_23.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install --no-install-recommends -y nodejs

## BACKEND
# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3.13 -
ENV PATH="${PATH}:/etc/poetry/bin"

# DBCA default Scripts
RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
RUN chmod 755 /tmp/default_script_installer.sh
RUN /tmp/default_script_installer.sh

## USER
# Create a non-root user
RUN groupadd -g 5000 appuser
RUN useradd --gid 5000 --uid 5000 --create-home --home-dir /home/appuser --no-log-init appuser
RUN echo 'alias ls="ls -lah --color=auto"' >> /home/appuser/.bash_aliases

# Create the app directory
RUN mkdir /app
RUN chown -R appuser:appuser /app

# =================== RUNTIME ===================
FROM builder_base

# Switch to non-root user
USER appuser
WORKDIR /app

# Copy backend code base
COPY --chown=appuser:appuser backend /app/

# Copy frontend code base (to a temp directory)
COPY --chown=appuser:appuser frontend /tmp/frontend/

# Install frontend dependencies & build assets
RUN cd /tmp/frontend; npm install; npm run build

# Copy frontend built assets before collecting static
RUN mkdir /app/assets;
RUN cp -r /tmp/frontend/dist/* /app/assets/

# Create virtualenv & install backend dependencies
# (this will always create the local `.venv` folder as per `poetry.toml` config)
RUN poetry install --no-root --no-interaction --no-ansi

# Use the virtualenv python from now on
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH=/app
WORKDIR /app

# Expose django app on port 8080
EXPOSE 8080

HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]

# Launch gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]

# Uncomment if you want to pause at some step
# (comment out until the pasue step)
# ENTRYPOINT ["sleep", "infinity"]