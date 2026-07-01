# DBCA Authorisations

Animal Ethics & Section 40/45 approval process

## Quick start

**Documentation is located in [docs/](docs/README.md).**

For setup and development instructions, start with [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

For testing, see the testing section in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) or the comprehensive guide at [docs/TESTING.md](docs/TESTING.md).

## Open source

This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.

Third-party dependency notices are maintained in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), with separate backend and frontend sections.

- **Contributing:** See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Security:** See [docs/SECURITY.md](docs/SECURITY.md)
- **Releases:** See [docs/RELEASE.md](docs/RELEASE.md)

## Purpose and domain

This system supports DBCA authorisation workflows, including Animal Ethics and Section 40/45 style application pathways. The platform is designed for versioned, process-driven forms where applicants submit applications backed by a questionnaire definition. A single authorisation process can include multiple questionnaire types (for example: New Application, Renewal) and each questionnaire type can have multiple versions over time.

## Overview

**Architecture & Design:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for data model, terminology, and design decisions.

**Backend Development:** See [docs/BACKEND-CONVENTIONS.md](docs/BACKEND-CONVENTIONS.md) for API layer, security, and ordering conventions.

**Frontend Development:** See [docs/FRONTEND-CONVENTIONS.md](docs/FRONTEND-CONVENTIONS.md) for React, TypeScript, and component guidelines.

**Application Flows:** See [docs/APPLICATION-FLOWS.md](docs/APPLICATION-FLOWS.md) for user journeys, routes, and workflows.

**File Management:** See [docs/FILE-MANAGEMENT.md](docs/FILE-MANAGEMENT.md) for attachment design and implementation.

**Deployment:** See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Kubernetes and kustomize configuration.

## Writing style

- Use British English spelling in code comments, docs, command names, and developer guidance.
- Prefer forms such as `normalise`, `normalisation`, and `authorisation`.

## Notable files

- `backend/entrypoint.sh` — Production startup sequence
- `backend/config/settings.py` — Environment and security configuration
- `backend/api/views.py` — Core DRF viewsets and queryset behaviour
- `backend/questionnaires/models.py` — Questionnaire data model and versioning
- `backend/questionnaires/admin.py` — Version clone-on-edit behaviour
- `backend/processes/models.py` — Process parent object and ordering
- `frontend/src/router.tsx` — Route definitions
- `frontend/src/context/ApiManager.ts` — API abstraction
