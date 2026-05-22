# End-to-End Tests (Playwright)

Playwright E2E tests that run against Django's pytest `live_server` with
real HTTP requests and browser interactions.

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

## E2E Spec Matrix

| ID | Spec | Role | Route/Endpoint | Primary Assertions |
|---|---|---|---|---|
| E2E-01 | Root redirect smoke | Anonymous | `GET /` | Redirects with `302` to `/my-applications`. |
| E2E-02 | SPA shell route availability | Applicant | `GET /my-applications`, `GET /new-application` | Returns `200` and renders SPA root container. |
| E2E-03 | Resume owner-only guard | Applicant/Reviewer | `GET /a/:key` | Owner gets `200`; reviewer gets `404`. |
| E2E-04 | Attachment read boundary | Applicant/Other Applicant | `GET /d/:appKey/:attachmentKey` | Owner can download; non-owner gets `404`. |
| E2E-05 | Assessment queue role scope | Reviewer/Applicant | `GET /api/assessment` | Reviewer sees queue item; applicant sees empty list. |
| E2E-06 | Assessment status transition | Reviewer | `PATCH /api/assessment/:key` | Valid reviewer update persists status change. |
| E2E-07 | Questionnaire latest selection | Anonymous | `GET /api/questionnaires` | Returns latest per `(process, code)` only. |
| E2E-08 | Application list owner scope | Applicant | `GET /api/applications` | Returns only caller-owned applications. |
| E2E-09 | Attachment filter validation | Applicant | `GET /api/attachments?application_key=...` | Invalid UUID returns `400`. |
| E2E-10 | Privacy consent create guard | Applicant | `POST /api/applications` | Missing consent is rejected with `400`. |
| E2E-11 | Verification token create guard | Applicant | `POST /api/applications` | Missing Turnstile token is rejected with `400`. |
| E2E-12 | Submit and read-only transition | Applicant | `PATCH/PUT /api/applications/:key` | Draft can be submitted; subsequent document update is rejected. |

## Implemented Test Files

- `e2e/tests/test_routing_smoke.py`
- `e2e/tests/test_api_contracts.py`
- `e2e/tests/test_access_and_assessment.py`
- `e2e/tests/test_application_lifecycle.py`
