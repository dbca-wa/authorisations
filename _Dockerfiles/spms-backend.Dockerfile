# syntax=docker/dockerfile:1
# ====================== IMAGE & CONFIG ======================

# Use the local version that works with poetry config when testing in dev (3.12.3)
# FROM python:3.12.6
FROM python:3.13.2
LABEL org.opencontainers.image.source=https://github.com/dbca-wa/science-project-service
# Ensures Python output sent to terminal for logging
ENV PYTHONUNBUFFERED=1
# Prevent additional .pyc files on disk
ENV PYTHONDONTWRITEBYTECODE=1
# Set timezone to Perth for logging
ENV TZ="Australia/Perth"

# ====================== OS LEVEL DEPENDENCIES & POSTGRES ======================

# RUN wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
RUN echo "Installing System Utils." && apt-get update && apt-get install -y \
    -o Acquire::Retries=4 --no-install-recommends \
    # postgresql postgresql-client \
    vim wget ncdu systemctl 
RUN apt-get upgrade -y

# Set working dir of project
WORKDIR /usr/src/app

# Install Poetry
RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
ENV PATH="${PATH}:/etc/poetry/bin"

# Prince Download
# RUN echo "Downloading Prince Package" \
#     && DEB_FILE=prince.deb \
#     && wget -O ${DEB_FILE} \
#     # https://www.princexml.com/download/prince_15.3-1_debian12_amd64.deb
#     https://www.princexml.com/download/prince_15.4.1-1_debian12_amd64.deb
RUN echo "Downloading and Installing Prince Package based on architecture" \
    && DEB_FILE=prince.deb \
    && ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ]; then \
    PRINCE_URL="https://www.princexml.com/download/prince_20250207-1_debian12_arm64.deb"; \
    #  https://www.princexml.com/download/prince_15.4.1-1_debian12_arm64.deb"; \
    else \
    PRINCE_URL="https://www.princexml.com/download/prince_20250207-1_debian12_amd64.deb"; \
    #  https://www.princexml.com/download/prince_15.4.1-1_debian12_amd64.deb"; \
    fi \
    && echo "Detected architecture: $ARCH, downloading from $PRINCE_URL" \
    && wget -O ${DEB_FILE} $PRINCE_URL 

# Prince installer
RUN apt-get update && apt-get install -y -o Acquire::Retries=4 --no-install-recommends \
    gdebi

# Install Prince
RUN echo "Installing Prince stuff" \
    && DEB_FILE=prince.deb \
    && yes | gdebi ${DEB_FILE}  \
    && echo "Cleaning up" \
    && rm -f ${DEB_FILE} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Prince location
ENV PATH="${PATH}:/usr/lib/prince/bin"

# Delete non-commercial license of Prince
RUN rm -f /usr/lib/prince/license/license.dat

# Create a symlink to the commercial license file
# Assumes that a valid Prince commercial license file is available in the backend/files directory
# Current license is set to expire on 31.05.2025
RUN ln -s /usr/src/app/backend/files/license.dat /usr/lib/prince/license/license.dat

# ====================== DEV FILES AND DEPENDENCIES ======================

# Move local files over
COPY . ./backend
WORKDIR /usr/src/app/backend

# Configure Poetry to not use virtualenv
RUN poetry config virtualenvs.create false
# Install deps from poetry lock file made in dev
RUN poetry install --no-root

# ====================== USER & PERMISSIONS ======================

# Create a non-root user to run the app
ARG UID=10001
ARG GID=10001
RUN groupadd -g "${GID}" spmsuser \
    && useradd --create-home --home-dir /home/spmsuser --no-log-init --uid "${UID}" --gid "${GID}" spmsuser

# Add the alias commands and configure the bash file
RUN echo '# Custom .bashrc modifications\n' \
    'fromdate="21.06.2024"\n' \
    'todate=$date\n' \
    'from=`echo $fromdate | awk -F\. '\''{print $3$2$1}'\''`\n' \
    'to=`echo $todate | awk -F\. '\''{print $3$2$1}'\''`\n' \
    'START_DATE=`date --date=$from +"%s"`\n' \
    'END_DATE=`date --date=$to +"%s"`\n' \
    'DAYS=$((($END_DATE - $START_DATE) / 86400 ))\n' \
    'RED='\''\033[0;31m'\''\n' \
    'GREEN='\''\033[0;32m'\''\n' \
    'PURPLE='\''\033[0;35m'\''\n' \
    'BLUEBG='\''\033[0;44m'\''\n' \
    'ORDBG='\''\033[0;48m'\''\n' \
    'GREENBG='\''\033[0;42m'\''\n' \
    'NC='\''\033[0m'\'' # No Color\n' \
    'LB='\''\e[94m'\'' # Light Blue\n' \
    'PS1="\n\n\[$(tput sgr0)\]\[\033[38;5;105m\]\d\[$(tput sgr0)\], \[$(tput sgr0)\]\[\033[38;5;15m\]\D{%H:%M:%S}\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;76m\]\w\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;10m\]--------------------------------\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;14m\]>\[$(tput sgr0)\]"\n' \
    'alias home="cd ~"\n' \
    'alias settz="export TZ=$TZ"\n' \
    'alias edit="home && vim .bashrc"\n' \
    'alias migrate="python manage.py makemigrations && python manage.py migrate"\n' \
    'settz\n' >> /home/spmsuser/.bashrc

# Ensure bashrc belongs to correct user and runs
RUN chown ${UID}:${GID} /home/spmsuser/.bashrc
# Own app
RUN chown -R ${UID}:${GID} /usr/src/app
RUN chown -R ${UID}:${GID} /usr/src/app/backend

# Own the Prince license file to update it later
RUN chown -R ${UID}:${GID} /usr/lib/prince/license
# Use Root Ensure entrypoint script can run for prince license and gunicorn
RUN chmod +x /usr/src/app/backend/entrypoint.sh

# ====================== LAUNCH ======================

# Switch to spmsuser (non-root)
USER ${UID}
# Expose and enter entry point (launch django app on p 8000)
EXPOSE 8000
# Set entrypoint
ENTRYPOINT ["/usr/src/app/backend/entrypoint.sh"]