# Feature Development Checklist

This document defines the **mandatory guidelines and checklist for all feature development and bug fixes**. AI agents and developers must follow these practices on every session unless explicitly told otherwise by the project owner.

---

## Before You Start

### 1. Understand the architecture and conventions

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the data model, terminology, and design decisions.
- Review [BACKEND-CONVENTIONS.md](BACKEND-CONVENTIONS.md) for backend patterns, security rules, and ordering constraints.
- Review [FRONTEND-CONVENTIONS.md](FRONTEND-CONVENTIONS.md) for React, TypeScript, and component guidelines.
- Check [APPLICATION-FLOWS.md](APPLICATION-FLOWS.md) for user journeys and authentication context.

### 2. Determine scope and layers

- Decide whether your feature affects frontend, backend, or both.
- Identify if new API endpoints or serializer changes are needed.
- Plan test coverage: unit, API, security, integration, and/or E2E.
- Identify if documentation updates are needed (README, guides, or architecture docs).

---

## Implementation Phase

### 1. Package managers — critical rule
- **Local development**: Use `bun` exclusively for all frontend commands (dev, lint, test, build)
- **CI/production/Docker**: Use `npm` (compatibility with container images and CI pipelines)
- **NEVER use `npm` for local development** — it negates the speed advantages of Bun and creates inconsistency
- **NEVER use `bun` in CI/Docker/production** — stick to `npm` for deterministic, reproducible builds

### 2. Code structure and style

#### Backend (Django/Python)
- API viewsets: `backend/api/views.py`
- Serializers: app `serialisers.py` (questionnaire serializer is an exception and lives with the model)
- Models: app `models.py`
- Management commands: `backend/{app}/management/commands/{command_name}.py`
- Use `select_related()` on known foreign-key paths for list/retrieve endpoints to prevent N+1 queries.

#### Frontend (React/TypeScript)
- Use `const` for React component definitions and function expressions (not `function` declarations).
- Use explicit named exports/imports over defaults for project modules (safer refactoring).
- Group imports: default imports first (no braces), then named/type imports (with braces), separated by blank line.
- Every function must have a JSDoc comment (`/** ... */`) explaining **what** it does and **why** it exists.
- Every critical logic block (guards, fallbacks, side effects) must have single-line comments explaining intent, not just restating code.
- Prefer British English in comments and code (e.g., `normalise`, `authorisation`).

#### Security (Backend)
- **Always** enforce owner scoping on application and attachment querysets.
- For **read** paths: use `Application.has_access(user)` (grants access to owner or reviewer-group members).
- For **write** paths: use explicit `application.owner == request.user` checks (no reviewers).
- Attachment deletions are soft-delete; include ownership checks.
- When adding an endpoint touching application data, explicitly decide: is this read (use `has_access`) or write (owner-only)?

#### API contracts
- Keep frontend type contracts aligned with API payloads.
- Process and questionnaire identifiers must be explicit and unambiguous.
- If changing serializer contracts, update frontend types and API manager calls in the same commit.

### 3. Code quality — syntax, types, and linting

**STOP before running tests.** Ensure code integrity first:

#### Backend
1. Check for Python syntax errors:
   ```bash
   cd backend && poetry run python -m py_compile path/to/file.py
   ```
2. Run type checking (if using mypy):
   ```bash
   cd backend && poetry run python -m mypy --config-file=pyproject.toml path/to/file.py
   ```

#### Frontend
1. Check TypeScript and linting (local development):
   ```bash
   cd frontend && bun run lint
   ```
   - This runs ESLint and TypeScript compiler with Bun (faster, same rules).
   - **For CI/production only**: `npm run lint` (when building Docker image or in CI pipelines).

2. Fix issues automatically:
   ```bash
   cd frontend && bun run lint -- --fix
   ```

3. Build check (catches type errors):
   ```bash
   cd frontend && bun run build
   ```
   - **For CI/production only**: `npm run build` (when building Docker image or in CI pipelines).

**Do NOT run tests until syntax and type checks pass.** Fix all errors first.

---

## Test Coverage

### Testing principles

- Add test coverage for **every new feature** and significant bugfix (unless explicitly exempted).
- Choose the smallest layer that validates behaviour: prefer unit > API > integration > E2E.
- Use deterministic fixtures and explicit waits; avoid brittle selectors or hidden global state.
- Prioritise test quality over quantity: target high-risk business outcomes and permission boundaries.

### When to add tests

| Feature type | Backend unit | Backend API | Backend security | Frontend unit | E2E | Required |
|---|---|---|---|---|---|---|
| New data model or logic | ✓ | | | | | Yes |
| New API endpoint | | ✓ | ✓* | | | Yes (API + security) |
| Read/write access change | | | ✓ | | | Yes (security) |
| New React component | | | | ✓ | | Yes |
| New dialog/modal/form workflow | ✓ | ✓ | | ✓ | ✓** | Yes (all) |
| Bugfix with ownership/permission implication | | | ✓ | | | Yes (security) |
| UI-only cosmetic change | | | | | | No |
| Documentation-only change | | | | | | No |

*Security test required if endpoint touches application data or has owner/reviewer rules.
**E2E required if workflow is mission-critical (e.g., application submission, assessment handoff).

### Test locations and commands

#### Backend tests

**All backend tests use** `cd backend && poetry run pytest` **from the backend directory.**

Structure:
- Unit/model tests: `backend/{app}/tests.py` or `backend/{app}/tests/test_*.py`
- API endpoint tests: `backend/api/tests/test_*.py`
- Security/view tests: `backend/{app}/test_views_security.py`
- Management command tests: `backend/{app}/tests/test_management_commands.py`
- E2E tests: `backend/e2e/tests/test_*.py`

Commands:
```bash
cd backend
# All backend tests
poetry run pytest

# Specific app
poetry run pytest applications -q

# Specific test file
poetry run pytest api/tests/test_views.py -v

# E2E tests only
poetry run pytest e2e/tests -v

# With coverage
poetry run pytest -n auto --cov --cov-report=term-missing --cov-report=html
```

#### Frontend tests

**For local development**, use `bun run test:unit` from the `frontend` directory.
**For CI/production**, use `npm run test:unit` (e.g., in Docker builds, CI pipelines).

Structure:
- Component unit tests: `frontend/src/test/unit/components/**/*.test.tsx`
- Context tests: `frontend/src/test/unit/context/**/*.test.tsx`
- Utility tests: `frontend/src/test/unit/**/*.test.ts`

Local development commands:
```bash
cd frontend
# Run all tests
bun run test:unit

# Coverage
bun run test:coverage
```

**CI/production commands** (in Docker, pipelines, or when npm is required):
```bash
cd frontend
# Run all tests
npm run test:unit

# Coverage
npm run test:coverage
```

#### E2E tests (optional, for mission-critical workflows)

```bash
cd backend
# Run E2E tests only
poetry run pytest e2e/tests -v

# With diagnostic traces and screenshots
poetry run pytest e2e/tests -v --tracing=retain-on-failure --screenshot=only-on-failure
```

### Backend test guidelines

- Security tests must verify both **positive** (access granted) and **negative** (access denied, 403/404) cases.
- Use realistic fixtures; avoid brittle hard-coded internal details.
- Test latest-version selection for questionnaires (ordering, cloning on edit).
- Test N+1 prevention: check that `select_related` is used on expected FK paths.

### Frontend test guidelines

- Test component props, state changes, and callbacks.
- Use accessibility-centric queries (`getByRole`, `getByLabelText`) instead of brittle CSS selectors.
- Test conditional rendering (e.g., sort option visibility, button disabled states).
- Mock external dependencies (API calls, contexts) with explicit factories, not implicit module mocks.
- Test error boundaries and fallback UI.

### E2E test guidelines

- Use E2E for mission-critical user journeys (e.g., application submission, assessment workflow).
- Use accessibility-centric selectors (`page.getByRole()`, `page.getByLabel()`).
- Explicit waits for UI state changes; avoid hard delays.
- One test = one business outcome; keep focused.
- Reuse authenticated state via storage_state per role (do not commit storage_state files with secrets).

---

## Documentation

### Code documentation

- Every function must have a comment block explaining what it does and why it exists.
  - **Backend**: Use Python docstrings.
  - **Frontend**: Use JSDoc blocks (`/** ... */`).
- Non-obvious logic must have single-line comments explaining **why**, not just restating the code.

### Project documentation updates

Update docs when your feature introduces new concepts, changes workflows, or adds user-facing behaviour:

- **ARCHITECTURE.md**: major data model changes, new entities, or core design decisions.
- **APPLICATION-FLOWS.md**: new routes, new authentication/permission rules, new user workflows.
- **BACKEND-CONVENTIONS.md**: new patterns, security rules, or gotchas specific to backend development.
- **FRONTEND-CONVENTIONS.md**: new component patterns, styling conventions, or frontend libraries.
- **DEVELOPMENT.md**: new setup steps, environment variables, or management commands.
- **FILE-MANAGEMENT.md**: changes to attachment handling or file storage.
- **TESTING.md**: new test layers, test infrastructure changes, or CI/CD patterns.

---

## CHANGELOG

### Format and rules

- **One entry per feature/fix**: summarise the user-facing impact in a single sentence.
- **Concise language**: explain what changed and why it matters, not technical implementation details.
- **Impact-focused**: e.g., "Added sorting options to application list" (good) vs "Refactored applicationUtils.tsx to extract sortApplications helper function" (too technical).
- **Consistent structure**: use categories: Added, Changed, Fixed, Removed (based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)).

### Version management

- Check the `VERSION` file and `CHANGELOG.md` to determine if you should add to an existing `Unreleased` version or create a new one.
- If the latest version in `CHANGELOG.md` has a past release date (compare with `VERSION`), that version has been released → create a new `[X.Y.Z] - Unreleased` section.
- If an `Unreleased` version already exists, add your entry to it.

### Example CHANGELOG entries

✓ Good:
```
- Added attachments dialog for technical officers to view and download application files from the assessment queue.
- Fixed attachment listing permissions so reviewers can see attachments for applications in authorised processes.
- Renamed application sort option "most recently updated" to "updated newest" for consistency.
```

✗ Avoid:
```
- Refactored applicationUtils.tsx to extract sortApplications and hasSubmittedApplications helper functions and added new parameter-driven defaults to getInitialSortOrder supporting per-page defaults and conditional rendering of sort options based on application data state.
```

---

## Pre-Submission Checklist

Before marking your work as ready:

- [ ] **Code quality**: No syntax errors, TypeScript/linting passes (`npm run lint`, type checks pass).
- [ ] **Tests written**: Unit/API/security/E2E as required for the feature (see [When to add tests](#when-to-add-tests)).
- [ ] **Tests passing**: Run full test suite for affected layers locally before pushing.
  - Backend: `cd backend && poetry run pytest`
  - Frontend: `cd frontend && npm run test:unit`
  - E2E (if applicable): `cd backend && poetry run pytest e2e/tests -v`
- [ ] **Documentation updated**: Code comments, README, architecture/convention docs, or TESTING.md as needed.
- [ ] **CHANGELOG entry**: Concise, impact-focused summary in `CHANGELOG.md` under the correct version.
- [ ] **Security**: Ownership/permission rules verified (if applicable).
- [ ] **API contracts**: Frontend types aligned with backend payloads (if applicable).
- [ ] **No breaking changes**: Existing tests still pass; migrations are reversible (if applicable).

---

## Overrides and Exceptions

AI agents and developers may skip specific items **only if explicitly instructed by the project owner**, e.g.:

- "Skip E2E for this feature."
- "No CHANGELOG entry needed for this bugfix."
- "No test coverage required for this documentation change."

**Unless explicitly told otherwise, all guidelines above are mandatory.**

---

## Quick Reference: Common Commands

### Backend

```bash
cd backend

# Run all tests
poetry run pytest

# Run specific app tests
poetry run pytest applications -q

# Run E2E tests
poetry run pytest e2e/tests -v

# Type check (if enabled)
python -m mypy --config-file=pyproject.toml path/to/file.py

# Dev server
poetry run python manage.py runserver

# Migrations
poetry run python manage.py migrate

# Create superuser
poetry run python manage.py createsuperuser
```

### Frontend (Local Development)

```bash
cd frontend

# Dev server
bun run dev

# Build
bun run build

# Lint and type check
bun run lint

# Tests
bun run test:unit

# Coverage
bun run test:coverage
```

**Note**: For CI/production (Docker, pipelines), use `npm` instead of `bun` (e.g., `npm run build`, `npm run test:unit`). See [DEVELOPMENT.md](DEVELOPMENT.md) and deployment docs for CI-specific commands.

---

**See [README.md](README.md) for the documentation index.**
