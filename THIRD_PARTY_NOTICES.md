# Third-Party Notices

This repository includes or depends on third-party software components.
This document records the primary direct dependencies used by the backend
and frontend applications, along with notable downstream licence signals
identified during the open source release review.

This file is informational and does not replace the licence terms of any
third-party component. Where a third-party licence imposes notice or
attribution obligations, those obligations continue to apply.

## Scope and maintenance

- Backend dependencies are managed in `backend/pyproject.toml` and installed in the Python environment.
- Frontend dependencies are managed in `frontend/package.json` and resolved via `frontend/package-lock.json`.
- The lists below focus on direct runtime dependencies because they are the clearest release boundary for this repository.
- Transitive dependency licences should continue to be reviewed during CI or release packaging.

## Backend direct dependencies

| Package | Version reviewed | Licence |
| --- | --- | --- |
| Django | 5.2.14 | BSD-3-Clause |
| psycopg | 3.3.4 | LGPL-3.0-only |
| django-vite | 3.1.0 | Apache-2.0 |
| whitenoise | 6.12.0 | MIT |
| gunicorn | 26.0.0 | MIT |
| django-environ | 0.14.0 | MIT |
| jsonschema | 4.26.0 | MIT |
| drf-jsonschema-serializer | 3.0.0 | BSD-3-Clause |
| django-jsonform | 2.23.2 | BSD-3-Clause |
| django-admin-tools | 0.9.3 | MIT |
| frozendict | 2.4.7 | LGPL-3.0-only |
| dbca-utils | 3.0.3 | Apache-2.0 |
| djangorestframework | 3.17.1 | BSD-3-Clause |
| pyfsig | 1.1.1 | MIT |
| django-storages | 1.14.6 | BSD-3-Clause |
| django-admin-sortable2 | 2.3.1 | MIT |
| requests | 2.33.1 | Apache-2.0 |

### Backend compliance notes

- `psycopg` and `frozendict` are LGPL-3.0-only. This does not require the repository itself to be relicensed under LGPL, but downstream distribution must still comply with the LGPL terms applicable to those components.
- The remaining reviewed backend direct dependencies are permissive licences commonly used in government and enterprise software.

## Frontend direct dependencies

| Package | Version reviewed | Licence |
| --- | --- | --- |
| @emotion/react | 11.14.0 | MIT |
| @emotion/styled | 11.14.1 | MIT |
| @mui/icons-material | 9.1.1 | MIT |
| @mui/material | 9.1.2 | MIT |
| @mui/x-data-grid | 9.7.0 | MIT |
| @mui/x-date-pickers | 9.7.0 | MIT |
| @tailwindcss/vite | 4.3.2 | MIT |
| axios | 1.18.1 | MIT |
| dayjs | 1.11.21 | MIT |
| react | 19.2.7 | MIT |
| react-dom | 19.2.7 | MIT |
| react-dropzone | 15.0.0 | MIT |
| react-hook-form | 7.80.0 | MIT |
| react-router | 7.18.1 | MIT |
| tailwindcss | 4.3.2 | MIT |
| underscore | 1.13.8 | MIT |
| uuid | 14.0.1 | MIT |

### Frontend transitive licence notes

The reviewed frontend lockfile also contains notable transitive licences and attribution-style content licences, including:

- MPL-2.0 packages used by the frontend build toolchain, including `lightningcss`.
- BlueOak-1.0.0 packages such as `lru-cache`, `minimatch`, and `sax`.
- CC-BY-4.0 content in `caniuse-lite`.
- CC0-1.0 data packages including `mdn-data` and `type-fest` metadata bundles.

These do not change the repository licence, but they should remain part of release-time licence scanning and attribution review.

## Review basis

The entries above were derived from:

- `backend/pyproject.toml`
- `frontend/package.json`
- `frontend/package-lock.json`
- installed Python package metadata in the backend virtual environment at review time

If dependencies change, update this file in the same change set.