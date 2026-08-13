# Command Patterns — Authoritative Reference

This document shows the standardized command patterns across the entire project. All documentation now follows these exact patterns.

---

## Local Development (Desktop/Laptop)

### Backend
```bash
# Syntax check
cd backend && poetry run python -m py_compile path/to/file.py

# Type checking
cd backend && poetry run python -m mypy --config-file=pyproject.toml path/to/file.py

# Tests
cd backend && poetry run pytest
cd backend && poetry run pytest applications -q
cd backend && poetry run pytest api/tests/test_views.py -v

# Run server
cd backend && poetry run python manage.py runserver

# Generate Django secret
cd backend && poetry run python -c 'import secrets; print(secrets.token_hex(25))'
```

### Frontend
```bash
# Dev server
cd frontend && npm run dev

# Linting (syntax + types)
cd frontend && npm run lint
cd frontend && npm run lint -- --fix

# Build
cd frontend && npm run build

# Tests (unit only)
cd frontend && npm run test:unit

# Tests (all)
cd frontend && npm run test

# Coverage
cd frontend && npm run test:coverage
```

### E2E (Local)
```bash
# Setup (frontend)
cd frontend && npm install && npm run build

# Setup (backend)
cd backend && poetry run python manage.py collectstatic --noinput

# Run tests (parallel execution across all CPU cores)
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope

# Run tests with diagnostic output (trace + screenshot on failure)
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope --tracing=retain-on-failure --screenshot=only-on-failure
```

---

## CI/Production (Docker, Pipelines, UAT)

### Frontend
```bash
# Install deps (in Dockerfile)
npm ci --no-audit --no-fund

# Build (in Dockerfile)
npm run build

# Tests
npm run test:unit
npm run test:coverage

# Lint
npm run lint
```

### Backend
```bash
# All commands remain the same (poetry run ...)
# No changes needed for CI/production context
```

---

## Key Rules

### Package Managers
- **All contexts**: Use `npm` exclusively (local development, CI, production, Docker)
- **No Bun**: Bun is not compatible with npm's dependency resolution; using both causes version mismatches
- **Why?**: npm's deterministic resolution ensures identical versions everywhere; Bun resolves optional/peer dependencies differently

### Python/Backend
- **Always use**: `cd backend && poetry run python ...`
- **Never use**: Direct `python` command
- **Virtual env**: Automatically activated by `poetry run`

### Test Commands
| Layer | Command |
|---|---|
| Backend unit/API | `cd backend && poetry run pytest` |
| Backend E2E | `cd backend && poetry run pytest e2e/tests -v` |
| Frontend unit | `cd frontend && npm run test:unit` |
| Frontend all | `cd frontend && npm run test` |

---

## Document Responsibility

| Document | Responsibility |
|---|---|
| **FEATURE-DEVELOPMENT.md** | ✓ PRIMARY - All command details |
| docs/DEVELOPMENT.md | Setup, quick references (links to FEATURE-DEVELOPMENT.md) |
| docs/TESTING.md | Architecture, CI flow (links to FEATURE-DEVELOPMENT.md) |
| docs/BACKEND-CONVENTIONS.md | Patterns, references FEATURE-DEVELOPMENT.md |
| docs/FRONTEND-CONVENTIONS.md | Patterns, references FEATURE-DEVELOPMENT.md |
| docs/CONTRIBUTING.md | Quick reference (links to FEATURE-DEVELOPMENT.md) |
| docs/RELEASE.md | Process, references FEATURE-DEVELOPMENT.md |

---

## Source of Truth

For **any question about commands**, refer to:
- **[docs/FEATURE-DEVELOPMENT.md](docs/FEATURE-DEVELOPMENT.md)** → Section "Quick Reference: Common Commands"

No other document contains the authoritative command patterns.
