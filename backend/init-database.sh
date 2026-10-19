#!/bin/bash
set -e

psql -U postgres -d postgres << SQL
CREATE USER authorisations_dev WITH PASSWORD '$DATABASE_PASSWORD';
CREATE DATABASE authorisations_dev OWNER authorisations_dev;
GRANT ALL PRIVILEGES ON DATABASE authorisations_dev TO authorisations_dev;
SQL
