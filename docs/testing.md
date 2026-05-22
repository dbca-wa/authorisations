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

### Backend Security Coverage

Added/expanded non-API Django view security testing in:
- backend/applications/test_views_security.py

Coverage focus:
- Owner-only resume flow.
- Read-only reviewer access via has_access for downloads.
- Soft-deleted attachment handling.
- Expected 404-style behaviour for unauthorised requests in these views.

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

### Frontend Shared UI/Context Coverage

Added focused tests in:
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
- request-driven E2E matrix covering routing, ownership, reviewer scope, assessment transitions, and draft lifecycle,
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

Current markers:
- unit
- api
- security
- integration
- slow
- smoke

Recommended E2E marker additions:
- e2e
- browser

Suggested execution patterns:
- local quick loop: unit/api/security/integration without e2e,
- pre-merge confidence: include e2e subset,
- nightly/regression: full e2e matrix and heavier artefacts.

## Local Commands

### Backend

Run all backend tests:
- cd backend && poetry run pytest

Run focused suites:
- cd backend && poetry run pytest applications -q
- cd backend && poetry run pytest questionnaires -q

### Frontend

Run frontend unit tests:
- cd frontend && bun run test:unit
- cd frontend && npm run test:unit

Run frontend coverage:
- cd frontend && bun run test:coverage
- cd frontend && npm run test:coverage

### E2E

Run E2E tests only:
- cd backend && poetry run pytest e2e/tests -v

Run E2E with richer diagnostics:
- cd backend && poetry run pytest e2e/tests -v --tracing=retain-on-failure --screenshot=only-on-failure

## CI Reference Flow

Recommended Validate stage order:
1. Backend tests and coverage.
2. Frontend lint/tests and coverage.
3. E2E browser tests with explicit browser install and JUnit output.
4. Coverage aggregation publish.

E2E CI checklist:
- Ensure Playwright browser install step exists.
- Ensure pytest writes JUnit XML when PublishTestResults expects it.
- Publish failure artefacts (trace/video/screenshots) for diagnosis.

## Extension Guide

When adding new tests:
- Choose smallest layer that can validate behaviour.
- Prefer deterministic fixtures over hidden global state.
- Add security checks whenever ownership/reviewer rules are involved.
- For browser tests, prioritise critical user journeys over exhaustive UI permutations.

When adding new E2E scenarios:
- Keep each test focused on one business outcome.
- Reuse setup helpers/fixtures.
- Use role-appropriate auth state.
- Assert both navigation and business outcome.

## Known Risks And Mitigations

Risk: Flaky E2E due to async UI timing.
- Mitigation: explicit waits and robust selectors.

Risk: Slow E2E suite growth.
- Mitigation: split smoke vs full regression sets.

Risk: Cross-test data leakage in browser/live-server tests.
- Mitigation: transactional DB mode and fixture discipline.

Risk: CI blind failures.
- Mitigation: trace-on-failure and published artefacts.

## Confidence Snapshot (May 2026)

Current confidence level: high for backend business rules and API/security boundaries, medium-high for frontend component logic.

Well-covered areas:
- Owner versus reviewer access rules (resume, download, assessment queue).
- Application lifecycle transitions (draft creation constraints, submit/read-only lock).
- Questionnaire latest-version selection and core API contract boundaries.
- Frontend form progression and shared dialog/snackbar/attachment interaction branches.

Remaining gaps to acknowledge:
- Full browser-hydrated E2E UI journeys are not yet the primary regression safety net; current E2E suite is intentionally request-driven for stability.
- Accessibility audits (keyboard flows, screen-reader announcements) are not yet systematically automated.
- Cross-browser matrix (beyond Chromium) is not yet part of routine CI validation.

Recommendation:
- Treat the current suite as release-capable for functional and security confidence, and schedule a dedicated follow-up stream for browser-hydration E2E and accessibility regression coverage.

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
- docs/testing.md (this document)
- docs/installation.md
- .github/copilot-instructions.md

## Maintenance Policy

- Keep this document updated when test architecture or CI behaviour changes.
- Keep high-level basics in copilot-instructions and installation docs; retain deep details here.
- If guidance conflicts, treat this file as the canonical testing reference and update cross-references.
