# End-to-End Tests (Playwright)

Minimal baseline setup for browser E2E testing with pytest and Playwright.

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

## Current Test Scope

- `e2e/tests/test_hello_world.py`: Dummy placeholder test that is guaranteed to pass.

## Next Step

Replace the placeholder with real browser-driven tests when you are ready.
