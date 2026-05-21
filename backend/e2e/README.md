# End-to-End Tests (Playwright)

Minimal Playwright E2E tests that run against Django's pytest `live_server`.

## Prerequisites

```bash
cd backend
poetry install --with dev
poetry run playwright install chromium
```

## Run E2E Tests

```bash
cd backend
poetry run pytest e2e/tests -v
```

No separate `manage.py runserver` is required.

Pytest uses `config.test_settings` (from `pyproject.toml`), while a normal
`manage.py runserver` uses `config.settings` unless you explicitly pass
`--settings=config.test_settings`.

## Current Test Scope

- `e2e/tests/test_hello_world.py`: Verifies `GET /` returns `302` with `Location: /my-applications`.

## Next Step

Add more real request-driven E2E tests against the local development server.
