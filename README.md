# DBCA Authorisations
Animal Ethics & Section 40/45 approval process

## Open source release documents

This repository is licensed under the Apache License 2.0. See `LICENSE` for the full licence text and `NOTICE` for repository-level attribution.

Third-party dependency notices are maintained in `THIRD_PARTY_NOTICES.md`, with separate backend and frontend sections to reflect the two build ecosystems used by this application.

Contributor and security guidance are available in `CONTRIBUTING.md` and `SECURITY.md`.

## Testing

Backend tests now run on `pytest` with categories for `unit`, `api`, `security`, `integration`, `slow`, and `smoke`. Pytest uses [backend/config/test_settings.py](backend/config/test_settings.py) so local and CI runs do not depend on PostgreSQL database-creation privileges.

Run the fast backend suite:

```bash
cd backend
poetry run pytest
```

Run backend tests in parallel with coverage:

```bash
cd backend
poetry run pytest -n auto --cov --cov-report=term-missing --cov-report=html --cov-report=xml
```

Run the frontend suite with Vitest:

```bash
cd frontend
bun run test
```

Run frontend coverage:

```bash
cd frontend
bun run test:coverage
```

Azure Pipelines now runs backend and frontend tests before the Docker build, and publishes coverage for both stacks.
