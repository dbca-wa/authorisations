# Testing Guide

This document is the canonical testing reference for the DBCA Authorisations project.

It consolidates:
- what has been implemented so far,
- what was learned while implementing it,
- best-practice guidance from Django, pytest-django, and Playwright,
- how to run tests locally and in CI,
- how to extend tests safely.

## Scope And Principles

The testing strategy is layered:
- Unit tests: model/domain logic, serializers, component logic.
- API tests: endpoint behaviours and response contracts.
- Security tests: access control and ownership rules.
- Integration tests: multi-layer interactions.
- End-to-end (E2E) tests: browser-driven user journeys against a live Django server.

Core principles:
- Keep fast tests fast; isolate slower browser tests.
- Use realistic fixtures while avoiding brittle hard-coded internals.
- Prefer deterministic selectors and explicit waits in browser tests.
- Keep ownership and permission checks central in security tests.
- Keep docs, CI, and local commands aligned.
- Prioritise test quality over quantity by targeting high-risk business outcomes and permission boundaries.

## What Was Implemented In This Session

### Backend Security Test Reorganization

Reorganized security tests for clarity with improved file naming:
- Renamed `test_security_nondisclosure_api.py` → `test_api_endpoint_security.py`
  - Tests API endpoint security: non-disclosure semantics, 404 responses for foreign records
  - Location: `backend/api/tests/test_api_endpoint_security.py`
  
Other security test locations:
- **API endpoint security**: `backend/api/tests/test_api_endpoint_security.py` (authorization, non-disclosure)
- **Non-API view security**: `backend/applications/test_views_security.py` (resume/download view access control)
- **Future**: `backend/e2e/tests/test_security/` for end-to-end security workflows

### Removed Test Duplication

Removed `test_application_create_rejects_invalid_turnstile_token` from `test_applications_api.py`
- **Reason**: Already covered comprehensively in `applications/tests.py::ApplicationSerialiserTurnstileTests`
- **Benefit**: Reduced redundancy; superior unit tests provide more thorough mock verification
- **Impact**: 119→118 backend tests (expected with consolidation)

### Management Command Coverage

Added command tests in:
- backend/questionnaires/tests/test_management_commands.py

Command covered:
- normalise_questionnaire_sort_order

Behaviour verified:
- Dry-run behaviour.
- Visible/latest ordering normalisation.
- Historical versions zeroed sort order.
- Idempotency on subsequent runs.

### Frontend Form Layout Coverage

Added/expanded tests in:
- frontend/src/test/unit/components/layout/form/form-layout.test.tsx

Key points verified:
- Required validation blocks progression.
- Step progression and navigation round-trip behaviour.
- Correct semantic querying for MUI components (for example, StepButton role tab).

### Frontend Backbone Module Coverage

Enhanced ApiManager.tsx test suite with focused endpoint coverage:
- **File**: `frontend/src/test/unit/context/api-manager.test.ts`
- **Tests added**: 9 additional test cases (from 4 to 13 total)
- **Coverage improvement**: All main endpoints covered (GET, POST, PUT, PATCH, DELETE)
  - Request configuration, error handling
  - Application, attachment, questionnaire, and process endpoints
  - FormData multipart uploads with progress callbacks
- **Frontend overall improvement**: 71.62% → 73.97% line coverage (with these tests + prior coverage)
- frontend/src/test/unit/components/common.test.tsx
- frontend/src/test/unit/context/dialogs-provider.test.tsx
- frontend/src/test/unit/context/snackbar-provider.test.tsx

Coverage focus:
- Attachment list rendering and edit-action visibility branches.
- Attachment delete success/error flows with snackbar and parent callbacks.
- Attachment rename flow with extension preservation and Enter-key submission.
- Dialog provider open/close behaviour, callback execution, and action rendering.
- Snackbar stacking, success/error duration branches, clickaway ignore behaviour, and timeout dismissal.

### E2E Infrastructure (Current Version)

Created E2E scaffolding under:
- backend/e2e/

Current implementation includes:
- in-memory SQLite with migration + fixture loading for deterministic E2E runs,
- authenticated Playwright request-context helpers with CSRF propagation,
- role-based fixture users and process/questionnaire/application seed data,
- request-driven E2E matrix covering routing, ownership, reviewer scope, review transitions, and draft lifecycle,
- resilient CI behaviour independent of PostgreSQL and frontend manifest coupling.

Implemented E2E files:
- backend/e2e/tests/test_routing_smoke.py
- backend/e2e/tests/test_api_contracts.py
- backend/e2e/tests/test_access_and_assessment.py
- backend/e2e/tests/test_application_lifecycle.py

## Research Findings And Best Practices

This section captures conclusions from reviewing official documentation and guidance from:
- Django testing documentation (5.2),
- pytest-django documentation,
- Playwright Python documentation.

### 1) Should E2E Be A Separate Module?

Yes, as a separate test suite boundary.

Clarification:
- A separate test package is good practice.
- It should be treated as testing infrastructure, not as a Django INSTALLED_APPS application.
- Good structure options include backend/e2e or backend/tests/e2e.

Important:
- Separation only helps if discovery and CI execution are also separated (marker/path based).

### 2) Live Server Management

Preferred approach:
- Use pytest-django live_server fixture for browser tests.

Why:
- live_server is designed for browser-functional tests.
- It handles a real HTTP server endpoint for Playwright/Selenium style clients.
- It integrates correctly with pytest-django transactional database requirements.

Anti-pattern to avoid:
- Assuming db transaction rollback from ordinary db fixtures will isolate state written through an independently running server process.

Note on static assets for browser tests:

When running E2E tests that use an actual browser context (Playwright `browser`),
the SPA static assets must be available to Django so the browser can load the
front-end shell. There are **two valid approaches**, each appropriate for different contexts:

#### Option A: Development Mode (Preferred for Local Development)

Run the Vite dev server alongside Django. This is the **recommended approach for development work**
because it enables:
- Hot module reloading (HMR) as you edit frontend code
- Faster iteration cycles
- Immediate feedback on component changes

Environment:
- `DJANGO_VITE_TEST_DEV_MODE=true` (default locally)
- Vite dev server listening on `http://localhost:5173`

Commands:
```bash
# Terminal 1: Start Vite dev server
cd frontend
npm run dev

# Terminal 2: Run E2E tests
cd backend
poetry run pytest e2e/tests -v --browser chromium
```

#### Option B: Static/Built Assets Mode (Used in CI)

Build the frontend, collect static assets, and run tests against the bundled code.
This mode mirrors production and is used in the CI pipeline.

Environment:
- `DJANGO_VITE_TEST_DEV_MODE=false`
- `DJANGO_VITE_TEST_MANIFEST_PATH=static/manifest.json`
- Frontend built to `frontend/dist/`
- Assets collected into `backend/static/` by Django's `collectstatic`

Commands:
```bash
# from the repository root
cd frontend
npm run build

cd ../backend
poetry run python manage.py collectstatic --noinput

# Run E2E tests against built assets
DJANGO_VITE_TEST_DEV_MODE=false DJANGO_VITE_TEST_MANIFEST_PATH=static/manifest.json \
  poetry run pytest e2e/tests -v --browser chromium
```

#### Why CI Uses Static Mode

The CI pipeline explicitly uses static/built assets because:
- No dependency on a separately-running dev server
- Validates that the production build works correctly
- Deterministic: tests run against exactly what users will deploy
- See `azure-pipelines.yml` E2E job for the full CI sequence

#### Summary

| Aspect | Dev Mode | Static Mode |
|--------|----------|-------------|
| **Best for** | Local development (preferred) | CI, final validation, production builds |
| **Setup** | `npm run dev` in separate terminal | `npm run build` + `collectstatic` |
| **Speed** | Fast iteration (HMR enabled) | Initial build slower; tests then run normally |
| **Frontend changes** | Hot reload works; immediate feedback | Must rebuild to see changes |
| **CI use** | Not typically used (dev server overhead) | Standard (no external dependencies) |

### 3) Database Isolation In Browser Tests

Key rule:
- Browser E2E tests should use transactional DB mode (or fixtures that imply it, such as live_server).

Reason:
- Server thread/process and test thread cannot share ordinary per-test transactional rollback semantics.

### 4) Playwright Fixture Architecture

Recommended fixture model:
- Session-scoped browser launch.
- Function-scoped context/page.
- New context per test for isolation.

Use plugin fixtures where possible:
- pytest-playwright provides browser/context/page fixtures and CLI/runtime options.

### 5) Authentication Strategy

Recommended model:
- Keep one UI-login smoke test.
- For most E2E tests, reuse authenticated state with storage_state files per role.

Security note:
- Do not commit storage_state artefacts with sensitive cookies/tokens.

### 6) Diagnostics And Artefacts

Preferred defaults in CI:
- Trace: retain-on-failure.
- Screenshot: only-on-failure (or off by default if traces are sufficient).
- Video: retain-on-failure for flaky/high-value paths only.

Notes:
- Video files are finalised when context closes.
- Traces are usually the most useful first-line debugging artefact.

### 7) Selector And Wait Strategy

Preferred selectors:
- get_by_role, get_by_label, and other accessibility-centric selectors.

Avoid:
- brittle CSS/text-only selectors that depend on implementation details.

Wait strategy:
- wait for explicit UI state changes that indicate readiness.

### 8) CI Best Practices For Playwright

CI E2E job should:
- install Python dependencies,
- install Playwright browser binaries,
- run frontend build if required for Django templates/static assets,
- execute only E2E tests by explicit path/marker,
- emit JUnit XML and publish results,
- publish trace/video/screenshot artefacts when available.

## Technical Learnings Captured During Implementation

### Backend/Test Environment

- Tests rendering Vite-backed templates require test-safe DJANGO_VITE config.
- Import-time settings still require baseline env vars in CI.
- SQLite in-memory and live-server/threaded tests have caveats; explicit waits are important.

### Frontend/Vitest

- vi.mock factories require mock symbols hoisted before usage.
- MUI accessibility roles may differ from naive assumptions.

### Pipeline

- UseNode@1 requires version, not versionSpec.
- Coverage should be published from a dedicated aggregation job to avoid overwrite behaviour.
- Avoid env keys beginning with SECRET_ in Azure script env mappings; prefer DJANGO_SECRET_KEY.

## Current Test Taxonomy

### Backend Markers

Current markers (used with `@pytest.mark`):
- `unit` — Unit/model logic tests
- `api` — API endpoint tests
- `security` — Security/authorization tests
- `integration` — Multi-layer integration tests
- `slow` — Slow-running tests (not run by default)
- `smoke` — Critical smoke tests
- `e2e` — End-to-end browser tests

Suggested execution patterns:
- **Local quick loop**: `pytest -m "not e2e and not slow"` (unit + api + security)
- **Pre-merge confidence**: Include e2e subset: `pytest -m "e2e" e2e/tests/`
- **Full validation**: `pytest` (all tests including slow)
- **Security focus**: `pytest -m security` (all security tests across layers)
- **Nightly/regression**: `pytest --cov` (with coverage report)

### Frontend Test Organization

By layer:
- **Unit**: Component logic, props, state, callbacks
- **Integration**: Multi-component interactions, context usage
- **Accessibility**: Queries (getByRole, getByLabel), keyboard interaction

By category:
- **Components**: Organized by input type and layout section
- **Context**: Providers, hooks, utilities
- **Router**: Navigation and route handling

## Security Test Locations (Quick Reference)

Finding where security tests belong:

| Security Aspect | File Location | Example |
|---|---|---|
| API endpoint authorization | `api/tests/test_api_endpoint_security.py` | `test_application_put_returns_404_for_non_owner` |
| Form/view access control | `applications/test_views_security.py` | `test_resume_application_returns_404_for_non_owner` |
| Assessor/reviewer access | Tests within API endpoint files | `test_reviewer_list_includes_only_processes_user_can_review` |
| E2E access workflows | `e2e/tests/test_security/` (planned) | Cross-layer permission verification |

## Local Commands

**For complete command reference, see [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md#quick-reference-common-commands).**

Quick reference:
- **Backend tests**: `cd backend && poetry run pytest`
- **Frontend tests**: `cd frontend && npm run test:unit`
- **E2E tests (dev mode, preferred)**: 
  - Terminal 1: `cd frontend && npm run dev` (start Vite dev server)
  - Terminal 2: `cd backend && poetry run pytest e2e/tests -v --browser chromium`
- **E2E tests (static mode, CI-style)**:
  - `cd frontend && npm run build && cd ../backend && poetry run python manage.py collectstatic --noinput`
  - `DJANGO_VITE_TEST_DEV_MODE=false DJANGO_VITE_TEST_MANIFEST_PATH=static/manifest.json poetry run pytest e2e/tests -v --browser chromium`

For coverage, diagnostics, and specific test patterns, refer to [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md#test-locations-and-commands).

## CI Reference Flow

Recommended Validate stage order:
1. Backend tests and coverage.
2. Frontend lint/tests and coverage.
3. E2E browser tests with explicit browser install and JUnit output.
4. Coverage aggregation publish.

E2E CI checklist:
- Ensure frontend is built: `npm run build` in CI before E2E job runs.
- Ensure Django collects static assets: `python manage.py collectstatic --noinput` in CI.
- Set environment variables for static mode: `DJANGO_VITE_TEST_DEV_MODE=false` and `DJANGO_VITE_TEST_MANIFEST_PATH=static/manifest.json`.
- Ensure Playwright browser install step exists: `poetry run playwright install --with-deps chromium`.
- Ensure pytest writes JUnit XML when PublishTestResults expects it.
- Publish failure artefacts (trace/video/screenshots) for diagnosis.

## Extension Guide

### Where to Add New Tests

When adding new features, follow these guidelines for test placement:

#### Backend Tests

**New API endpoint?**
- Add tests to `backend/api/tests/test_{endpoint_name}_api.py`
- Example: New `/api/reviews` endpoint → `backend/api/tests/test_reviews_api.py`
- Include both success and error cases; security/authorization tests follow below

**New API endpoint with authorization?**
- Add security tests to `backend/api/tests/test_api_endpoint_security.py`
- Template: `test_{resource}_{operation}_returns_404_for_non_owner`
- Example: `test_review_patch_returns_404_for_non_owner`

**Non-API Django view (form, download, etc.)?**
- Add security tests to `backend/applications/test_views_security.py` (or create similar for other apps)
- Template: `test_{view_name}_returns_404_for_{access_type}`
- Example: `test_download_returns_404_for_non_reviewer`

**Model method or data logic?**
- Add unit tests to `backend/{app}/tests/test_models.py`
- Coverage: Test all code branches, edge cases, and error conditions

**Serializer logic?**
- Add unit tests to `backend/{app}/tests/test_serialisers.py`
- Coverage: Field validation, transformation, error messages

**Management command?**
- Add tests to `backend/{app}/tests/test_management_commands.py`
- Coverage: Success paths, dry-run behavior, idempotency

**Multi-layer integration (API + model + permissions)?**
- Add E2E tests to `backend/e2e/tests/test_{workflow_name}.py`
- Example: Application submission workflow → `backend/e2e/tests/test_application_submission.py`
- Or add to `backend/e2e/tests/test_security/test_{security_scenario}.py` for access control scenarios

#### Frontend Tests

**New React component?**
- Add unit tests to `frontend/src/test/unit/components/{category}/{component_name}.test.tsx`
- Use accessibility-centric selectors: `getByRole`, `getByLabelText`, `getByTitle`
- Example: New form input → `frontend/src/test/unit/components/inputs/email-input.test.tsx`

**New dialog/modal?**
- Add tests to component's dedicated test file
- Also test interaction in parent component where it's triggered
- Verify dialog lifecycle: open, interaction, close

**New utility function?**
- Add tests to `frontend/src/test/unit/{utility_category}/{function_name}.test.ts`
- Example: New application filter → `frontend/src/test/unit/utils/application-filters.test.ts`

**New context/provider?**
- Add tests to `frontend/src/test/unit/context/{context_name}.test.tsx`
- Coverage: Provider setup, hooks, state updates, error states
- Example: See `dialogs-provider.test.tsx` for template

**API integration?**
- Add tests to `frontend/src/test/unit/context/api-manager-comprehensive.test.ts`
- Or create focused integration tests in component test file
- Mock ApiManager methods with vi.mock

**Router/Navigation changes?**
- Add tests to `frontend/src/test/unit/router/router.test.tsx`
- Coverage: Route matching, redirects, parameter handling

### Test Quality Checklist

Use this when writing new tests:

**Backend**:
- [ ] Test both success and failure paths
- [ ] Include security/authorization tests for operations on user data
- [ ] Use realistic fixtures; avoid hard-coded magic numbers
- [ ] Verify query optimization (select_related for FK queries)
- [ ] Check that error messages are user-friendly

**Frontend**:
- [ ] Use accessibility-centric queries (no brittle CSS selectors)
- [ ] Test props, state changes, callbacks
- [ ] Mock external dependencies (API calls, contexts)
- [ ] Include error boundary and fallback UI tests
- [ ] Verify button/form disabled states

**Security**:
- [ ] Test positive case (access granted, 200/201)
- [ ] Test negative case (access denied, 403/404)
- [ ] Verify foreign resource returns 404 (non-disclosure)
- [ ] Test both owner and non-owner scenarios

### Updating This Section

When adding new patterns, update this guide to help future developers
and ensure AI agents place tests in the correct locations.

When adding new test file, follow naming:
- `test_{subject}_{aspect}.py` (backend)
- `{component_name}.test.tsx` (frontend components)
- Avoid generic names; be specific about what the file tests

## Known Risks And Mitigations

Risk: Flaky E2E due to async UI timing.
- Mitigation: explicit waits and robust selectors.

Risk: Slow E2E suite growth.
- Mitigation: split smoke vs full regression sets.

Risk: Cross-test data leakage in browser/live-server tests.
- Mitigation: transactional DB mode and fixture discipline.

Risk: CI blind failures.
- Mitigation: trace-on-failure and published artefacts.

## Confidence Snapshot (July 2026)

Current confidence level: **high** for backend business rules and API/security boundaries,
**high** for frontend API layer, **medium-high** for frontend component logic.

Well-covered areas:
- **Backend**: Owner versus reviewer access rules, application lifecycle transitions, questionnaire versioning
- **Frontend API layer**: All ApiManager endpoints (100% coverage), request configuration, error handling
- **Frontend components**: Form progression, dialog/snackbar/attachment interaction branches, accessibility semantics

Remaining gaps to acknowledge:
- **Backend**: applications/models.py (39% coverage) — core data model methods need expansion
- **Frontend**: MyApplications, FileInput, Grid components (50-60% coverage) — workflow edge cases
- **E2E**: Full browser-hydrated test coverage not yet primary regression safety net; current suite is request-driven for stability
- **Accessibility**: Keyboard flows and screen-reader announcements not yet systematically automated

Recommendation:
- Current suite is **release-capable** for functional and security confidence
- Continue improving module coverage toward 80%+ line coverage target
- Plan dedicated E2E browser-hydration stream for UI journey regression coverage
- Schedule accessibility audit and keyboard flow testing

## File Map (Testing-Relevant)

Backend:
- backend/pyproject.toml
- backend/config/test_settings.py
- backend/conftest.py
- backend/e2e/conftest.py
- backend/e2e/tests/

Frontend:
- frontend/src/test/
- frontend/vitest.config.ts (if present)

CI:
- azure-pipelines.yml

Project docs:
- docs/TESTING.md (this document)
- docs/DEVELOPMENT.md
- ../README.md

## Maintenance Policy

- Keep this document updated when test architecture or CI behaviour changes.
- Keep high-level basics in copilot-instructions and installation docs; retain deep details here.
- If guidance conflicts, treat this file as the canonical testing reference and update cross-references.
