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
| Django | 5.2.17 | BSD-3-Clause |
| psycopg | 3.3.6 | LGPL-3.0-only |
| django-vite | 3.2.0 | Apache-2.0 |
| whitenoise | 6.9.0 | MIT |
| gunicorn | 26.2.0 | MIT |
| django-environ | 0.14.0 | MIT |
| jsonschema | 4.26.0 | MIT |
| drf-jsonschema-serializer | 3.0.0 | BSD-3-Clause |
| django-jsonform | 2.23.2 | BSD-3-Clause |
| django-admin-tools | 0.9.3 | MIT |
| frozendict | 2.4.7 | LGPL-3.0-only |
| dbca-utils | 3.0.13 | Apache-2.0 |
| djangorestframework | 3.18.1 | BSD-3-Clause |
| pyfsig | 1.1.1 | MIT |
| django-storages | 1.14.6 | BSD-3-Clause |
| django-admin-sortable2 | 2.3.1 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| idna | 3.20 | BSD-3-Clause |

### Backend compliance notes

- `psycopg` and `frozendict` are LGPL-3.0-only. This does not require the repository itself to be relicensed under LGPL, but downstream distribution must still comply with the LGPL terms applicable to those components.
- The remaining reviewed backend direct dependencies are permissive licences commonly used in government and enterprise software.

## Frontend direct dependencies

### Runtime dependencies
| Package | Version reviewed | Licence |
| --- | --- | --- |
| @emotion/react | 11.14.0 | MIT |
| @emotion/styled | 11.14.1 | MIT |
| @mui/icons-material | 9.4.0 | MIT |
| @mui/material | 9.4.0 | MIT |
| @mui/x-data-grid | 9.14.0 | MIT |
| @mui/x-date-pickers | 9.14.0 | MIT |
| @tailwindcss/vite | 4.3.3 | MIT |
| axios | 1.20.0 | MIT |
| canvas-confetti | 1.9.4 | ISC |
| dayjs | 1.11.23 | MIT |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| react-dropzone | 20.1.2 | MIT |
| react-hook-form | 7.89.0 | MIT |
| react-router | 8.4.0 | MIT |
| tailwindcss | 4.3.3 | MIT |
| underscore | 1.13.8 | MIT |
| uuid | 14.0.2 | MIT |

### Development dependencies (devDependencies)
| Package | Version reviewed | Licence |
| --- | --- | --- |
| @eslint/js | 10.0.1 | MIT |
| @iconify-json/flat-color-icons | 1.2.3 | MIT |
| @iconify-json/vscode-icons | 1.2.81 | MIT |
| @iconify/tailwind4 | 1.2.3 | MIT |
| @testing-library/dom | 10.4.0 | MIT |
| @testing-library/jest-dom | 7.0.1 | MIT |
| @testing-library/react | 16.3.3 | MIT |
| @testing-library/user-event | 14.6.7 | MIT |
| @types/canvas-confetti | 1.9.0 | MIT |
| @types/node | 26.6.3 | MIT |
| @types/react | 19.3.0 | MIT |
| @types/react-dom | 19.3.0 | MIT |
| @types/underscore | 1.13.0 | MIT |
| @types/use-sync-external-store | 1.7.0 | MIT |
| @vitejs/plugin-react | 6.1.1 | MIT |
| @vitest/coverage-istanbul | 4.1.10 | MIT |
| eslint | 10.11.0 | MIT |
| eslint-plugin-react-hooks | 7.1.1 | MIT |
| eslint-plugin-react-refresh | 0.5.7 | MIT |
| globals | 17.12.0 | MIT |
| jsdom | 30.1.1 | MIT |
| msw | 3.0.0 | MIT |
| typescript | 6.0.3 | Apache-2.0 |
| typescript-eslint | 8.71.0 | BSD-2-Clause |
| vite | 8.3.1 | MIT |
| vitest | 4.1.10 | MIT |

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