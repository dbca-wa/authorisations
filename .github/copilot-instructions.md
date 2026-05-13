# Copilot Instructions for DBCA Authorisations

## Purpose And Domain
- This system supports DBCA authorisation workflows, including Animal Ethics and Section 40/45 style application pathways.
- The platform is designed for versioned, process-driven forms where applicants submit applications that are backed by a questionnaire definition.
- A single authorisation process can include multiple questionnaire types (for example: New Application, Renewal) and each questionnaire type can have multiple versions over time.

## Writing Style
- Use British English spelling in code comments, docs, command names, and developer guidance.
- Prefer forms such as `normalise`, `normalisation`, and `authorisation`.

## Code Comment Conventions
- Every new function — regardless of size — must have a docstring comment directly above or inside it that explains **what the function does** and why it exists.
  - For TypeScript/React: use a `/** ... */` JSDoc block before the function.
  - For Python: use a `"""Docstring."""` inside the function body.
- Every critical part within a function (non-obvious logic, guards, fallbacks, side effects) must have one or two single-line comments explaining the intent, not just restating the code.
- Comments should explain **why**, not just **what**.

## Current Canonical Terminology
- `AuthorisationProcess`:
  - Parent domain object that groups related questionnaires under a business process.
  - Owns stable process identity via `slug` and display ordering via `sort_order`.
- `Questionnaire`:
  - Versioned schema/content definition used to build application forms.
  - Belongs to one `AuthorisationProcess`.
  - Has a business `name` (questionnaire kind within the process), `version`, and `sort_order`.
- `Application`:
  - User-owned submitted/draft record tied to one specific questionnaire version.
- `ApplicationAttachment`:
  - File metadata linked to an application, soft deletable.

### Terminology Migration Notes
- Historical/legacy mental model treated questionnaire `slug` as top-level identity.
- Current model treats process `slug` as process identity and questionnaire `id` as concrete questionnaire identity.
- For stable evolution, prefer explicit questionnaire identity (`id`) in create/update flows where ambiguity exists.

## Architecture
- Backend:
  - Django 5.2, Django REST Framework, PostgreSQL.
  - Modular apps under `backend/`: `applications`, `questionnaires`, `processes`, `api`, `users`, `dbnow`.
- Frontend:
  - React + TypeScript + Vite + MUI + Tailwind.
  - Routing in `frontend/src/router.tsx`.
  - API access abstraction in `frontend/src/context/ApiManager.ts`.
- Deployment/runtime:
  - Docker supported.
  - Backend startup orchestration in `backend/entrypoint.sh` (collectstatic, migrate, gunicorn).

## Business Logic Behind Technical Structure

### Why `AuthorisationProcess` Exists
- Business users need a process-level grouping independent of questionnaire revisions.
- Process metadata (name, description, image, sort order, slug) should remain stable while questionnaires evolve.
- Process-level grouping improves applicant UX by presenting clear process categories before selecting questionnaire type.

### Why `Questionnaire` Is Versioned
- Regulatory/business forms evolve over time and old applications must remain linked to the exact questionnaire version they were created from.
- Version cloning in admin preserves immutable history while allowing updates to produce a new latest version.
- Latest version selection is a read concern; historical version retention is a compliance/audit concern.

### Why Distinct Latest Selection Is Explicit
- Requirement: list one active/latest questionnaire per `(process, questionnaire name)`.
- PostgreSQL `DISTINCT ON` semantics enforce strict alignment between `DISTINCT ON` columns and initial `ORDER BY` columns.
- Therefore latest-selection ordering and final display ordering are often separate concerns and may require a two-step queryset pattern.

### Why Ordering Is Managed Carefully
- `sort_order` on process and questionnaire encodes curated display sequence.
- Third-party admin drag-and-drop integration (`django-admin-sortable2`) expects the primary sortable field to be a concrete local model attribute.
- Relation traversals in model `Meta.ordering` (for example `process__sort_order`) may be valid in Django ORM, but can break plugin internals that do `getattr(obj, field_name)`.

## Data Relationships (Important)

### Core Relationship Graph
- One `AuthorisationProcess` has many `Questionnaire` records.
- One `Questionnaire` belongs to exactly one `AuthorisationProcess`.
- One `Questionnaire` can have many `Application` records.
- One `Application` belongs to exactly one `Questionnaire` and one owner (`users.User`).
- One `Application` has many `ApplicationAttachment` records.
- One `ApplicationAttachment` belongs to exactly one `Application`.

### Key Questionnaire Invariants
- Questionnaire uniqueness/versioning invariant:
  - Unique constraint includes `(process, name, version DESC expression)` by name `qnaire_unique_process_name_version_desc`.
- Operational meaning:
  - For each `(process, name)`, there may be multiple rows by version.
  - "Latest" is determined by highest `version` for that pair.

## Backend Conventions

### API Layer
- DRF viewsets are in `backend/api/views.py`.
- Serializers are primarily in app `serialisers.py`; questionnaire serializer intentionally sits with model due to schema import/circular dependency constraints.
- Prefer `select_related` on known foreign-key paths for list/retrieve endpoints to avoid N+1 behavior.

### Security And Ownership
- Application and attachment querysets must always enforce owner scoping.
- Attachment deletions are soft-delete and must include ownership checks.
- CSRF behavior includes project-specific configuration and has known interactions with third-party admin endpoints.

### Read Access vs Write Access (`has_access` vs owner check)
- `Application.has_access(user)` grants **read** access. Two principals qualify:
  1. The application owner.
  2. Any authenticated user whose groups intersect the process's `reviewer_groups` (technical officers / assessors).
- `has_access` must **not** be used as the guard for write/mutation paths.
  - `resume_application` (the interactive form URL) uses an explicit `application.owner == request.user` check so that reviewers cannot open and modify someone else's application through the form.
  - `download_application` and `download_attachment` correctly use `has_access` because those are read-only operations.
- Whenever adding a new endpoint or view that touches application data, decide explicitly: is this a read path (use `has_access`) or a write/owner-only path (use explicit `owner == user` check)?

### Ordering Rules
- Keep model `Meta.ordering` simple and local-field based when sortable admin integrations are used.
- Use explicit queryset ordering in API/admin where relation-based ordering is needed.
- Do not assume one ordering expression can satisfy both:
  - latest row selection by grouping key
  - final display order

## Admin Behavior

### Questionnaire Admin Intent
- Admin edits clone on change:
  - Increment version, set `pk=None`, persist as new row.
- Read-only fields protect immutable dimensions for existing versions.
- Add/change action buttons are intentionally simplified for workflow control.

### `django-admin-sortable2` Constraints
- First ordering field used by sortable mixin must be writable concrete field on the model (for this project: `sort_order`).
- Do not make sortable admin depend on relation traversal ordering key.
- If relation-based display ordering is needed, use queryset-level `.order_by(...)` for read paths, not sortable field identity.

## Frontend Conventions
- New application flow is process-centric:
  - Present processes first.
  - Then present questionnaire choices under each process.
- Keep frontend type contracts aligned with API payloads:
  - Process identifiers and questionnaire identifiers must be explicit and unambiguous.
- Use `dayjs` for dates with `en-au` locale.
- Prefer React component definitions as `const` (for example `const MyComponent = () => { ... }`) rather than `function` declarations unless there is a clear technical reason to do otherwise.
- Prefer frontend function expressions assigned to `const` (including hooks and local helpers) rather than `function` declarations unless there is a clear technical reason (for example hoisting requirements).
- Prefer explicit named exports/imports over default exports/imports for project modules where practical, to make refactoring safer and imports more consistent.
- Group imports by style with a single blank line separating default imports from named/type imports:
  - First block: default imports (no curly braces), for example `import React from "react"` or `import Box from "@mui/material/Box"`.
  - Second block: named and type imports (with curly braces), for example `import { useState } from "react"` or `import type { AlertColor } from "@mui/material/Alert"`.
  - This separation is purely organisational — it makes the import block easier to scan at a glance and reflects the technical distinction between default and named exports.

## Integration Contracts

### Frontend <-> Backend
- REST API is the integration boundary.
- CSRF header behavior is configurable and can impact third-party components.
- Process and questionnaire contracts must stay in sync when changing lookup semantics.

### External Dependencies
- PostgreSQL behavior matters for DISTINCT and ORDER BY query design.
- `django-admin-sortable2` used for admin ordering UX; plugin limitations should be accounted for in model/admin configuration.

## PDF Icon CSS Build Contract

### Why `pdf-icons.css` Exists
- The application PDF renders file-type icons that must match frontend icon mapping logic.
- Prince renders the PDF without relying on runtime HTTP fetches for this icon stylesheet.
- A dedicated Vite entry builds a stable output file named `pdf-icons.css` so Django staticfiles can always find it by that exact name.

### How It Is Generated
- Source entry is `frontend/src/pdf-icons.css`.
- Vite includes a dedicated build input named `pdf-icons` and emits hash-free `pdf-icons.css`.
- Tailwind v4 scans explicit sources declared in `pdf-icons.css`:
  - `backend/applications/models.py` (icon class mapping values)
  - `backend/templates/application-pdf-template.html` (base icon class usage)
- During PDF context building, backend code loads `pdf-icons.css` via Django staticfiles finder and inlines it into the template.

### Docker Build Path Requirement (Critical)
- `frontend/src/pdf-icons.css` uses relative `@source` paths that assume:
  - frontend source is available at `/tmp/frontend`
  - backend source is available at `/tmp/backend`
- Therefore Docker builds that run `npm run build` for frontend must copy both source trees into those temporary locations before the build step.
- If either source path is missing, Tailwind cannot resolve icon class sources and the generated `pdf-icons.css` will be incomplete or incorrect.

### Safe Change Checklist
- If moving directories or changing Docker stages, preserve the relative source relationship used by `pdf-icons.css`.
- If adding new attachment file types, update `_EXTENSION_TO_ICON_CLASS` in `backend/applications/models.py` and rebuild frontend assets.
- After build changes, verify that output contains `pdf-icons.css` and that generated PDFs still show correct file-type icons.

## Known Gotchas And Learnings

### Distinct On (PostgreSQL)
- Error pattern: `SELECT DISTINCT ON expressions must match initial ORDER BY expressions`.
- Root cause: order prefix mismatch against distinct fields.
- Safe pattern for latest-per-group:
  - first select by `order_by(group_fields..., -version).distinct(group_fields...)`
  - then apply final display order in outer queryset if needed.

### Relation In `Meta.ordering`
- Django supports relation ordering in many ORM contexts.
- Some admin/plugin internals may treat ordering key as direct object attribute, causing runtime attribute errors.
- Practical recommendation in this codebase:
  - keep `Meta.ordering` local/simple
  - apply relation ordering explicitly in querysets where required.

### Sortable2 Compatibility
- Library internals rely on writable field operations (`getattr/setattr/bulk_update`) against the default sortable field.
- Relation traversals are not writable sortable fields.

### Questionnaire Sort Order Normalisation Command
- Command: `normalise_questionnaire_sort_order`
- Purpose:
  - Rebuild `Questionnaire.sort_order` values globally with a visible/latest-first policy.
  - Recover from corrupted ordering states (for example many rows at `0`, gaps, duplicates, negative values).
- Behavior:
  - Determines current visible questionnaire order from latest versions by existing `sort_order`.
  - Reassigns latest versions to contiguous visible ranks `1..N` in that preserved global order.
  - Sets all historical (non-latest) versions to `0` so they do not interfere with visible ordering.
  - Updates only rows that need change.
  - Safe and idempotent: repeated runs converge to the same result and make no further updates once normalised.
- Operational note:
  - Prefer this command over `manage.py reorder questionnaires.Questionnaire` for this model, because `reorder` uses `Meta.ordering[0]` and may target non-sort fields.

### Azure Pipelines Secret Prefix Filtering
- Azure Pipelines can filter script environment variable names that begin with reserved prefixes, including `secret` (case-insensitive).
- Practical impact observed in this project:
  - `SECRET_KEY` in a script `env:` block arrives empty in bash even when the source pipeline variable is set.
  - `DJANGO_SECRET_KEY` in the same `env:` block arrives correctly.
- Safe pattern for this codebase:
  - Do not map script env keys that begin with `SECRET_`.
  - Map `DJANGO_SECRET_KEY` in pipeline YAML and read it first in Django settings, with `SECRET_KEY` fallback for local compatibility.

### Docker@2 `buildAndPush` And Build Arguments
- In this project, `Docker@2` with `command: buildAndPush` did not reliably pass `arguments` (for example `--build-arg LOCAL_MEDIA_STORAGE=...`) to the Docker build.
- Symptom:
  - Pipeline debug step shows `LOCAL_MEDIA_STORAGE` is set.
  - Dockerfile step before `collectstatic` sees `LOCAL_MEDIA_STORAGE(raw)=''`.
- Safe pattern for this codebase:
  - Use `Docker@2` `command: build` with `arguments`, followed by `Docker@2` `command: push` in the same job.
  - Keep build and push in the same job so the local image remains available for push.

### Docker Image Availability Across Jobs
- Docker images built on Microsoft-hosted agents are not shared across jobs/stages.
- Symptom:
  - Push job logs `An image does not exist locally with the tag ...` when build and push are split across different jobs/stages.
- Safe pattern for this codebase:
  - Keep Docker build and Docker push in the same job.
  - If stages must be split, explicitly transfer image artifacts (`docker save` / `docker load`).

### Node Task Migration Gotcha (`UseNode@1`)
- `NodeTool@0` is deprecated and should be replaced with `UseNode@1`.
- `UseNode@1` expects input key `version` (not `versionSpec`).
- Symptom when misconfigured:
  - Task label says Node 22, but agent installs default Node 10.x.
  - Frontend `npm ci` fails with dependency-resolution/runtime errors.
- Safe pattern for this codebase:
  - Use:
    - task: `UseNode@1`
    - inputs: `version: '22.x'`

### Coverage Publish Overwrite Behaviour
- Publishing backend and frontend coverage independently can lead Azure DevOps Code Coverage tab to show only the last published dataset.
- Symptom:
  - Coverage tab shows only frontend (`.tsx`) or only backend files depending on publish order.
- Safe pattern for this codebase:
  - Publish raw coverage XML from each test job as pipeline artifacts.
  - Add a dedicated downstream `Coverage` job that downloads both artifacts and runs a single `PublishCodeCoverageResults@2` step.

## Development Workflows

### Backend Commands
- Run dev server: `cd backend && poetry run python manage.py runserver`
- Run tests: `cd backend && poetry run python manage.py test`
- Run migrations: `cd backend && poetry run python manage.py migrate`
- Collect static: `cd backend && poetry run python manage.py collectstatic`
- Normalise questionnaire sort order globally:
  - `cd backend && poetry run python manage.py normalise_questionnaire_sort_order`
  - Dry-run mode: `cd backend && poetry run python manage.py normalise_questionnaire_sort_order --dry-run`

### Frontend Commands
- Package manager policy:
  - Use Bun for local development workflows because it is faster and supports npm-compatible scripts.
  - Use npm for UAT, production, and CI environments to keep deployment/runtime behaviour consistent.
- Run dev server (local development): `cd frontend && bun run dev`
- Build (UAT/production/CI): `cd frontend && npm run build`
- Lint (UAT/production/CI): `cd frontend && npm run lint`

### CI/CD Pipeline Policy
- Azure Pipelines YAML is hosted in GitHub, so CI and PR trigger behaviour is controlled in `azure-pipelines.yml` rather than Azure Repos branch policies.
- CI should run on direct pushes to `main`, `uat`, and `feature/*` branches.
- Pull request triggered pipeline runs are intentionally disabled with `pr: none` to avoid duplicate runs when a feature branch already has push-based CI.
- Feature branch workflow expectation:
  - push to `feature/*` runs the full test pipeline once.
  - opening or updating a PR from that feature branch should not start a second PR-validation pipeline.
- The Docker build and push steps may still keep a `Build.Reason != PullRequest` condition as a defensive guard, but PR suppression should be enforced primarily by `pr: none`.
- When Docker build arguments are required (for example env used during `collectstatic`), prefer `Docker@2 build` then `Docker@2 push` in one job instead of `buildAndPush`.
- For script steps, do not use environment variable keys beginning with `SECRET_`; use `DJANGO_SECRET_KEY` and map to Django settings accordingly.
- For frontend CI Node setup, use `UseNode@1` with `version: '22.x'`.
- For code coverage, publish once from a dedicated aggregation job rather than publishing separately from backend and frontend jobs.

### CI Test Environment Requirements
- Backend pytest uses `config.test_settings`, which imports `config.settings` first.
- Import-time settings evaluation still requires baseline env vars before test overrides apply.
- Safe pattern for this codebase in CI backend test job:
  - set `DATABASE_URL` to SQLite (`sqlite:///:memory:`)
  - pass `DJANGO_SECRET_KEY`
  - set `LOCAL_MEDIA_STORAGE='true'`
  - set `PRIVATE_MEDIA_ROOT` to a writable temp path (for example `/tmp/private-media`)

## Notable Files
- `backend/entrypoint.sh`:
  - Production startup sequence.
- `backend/config/settings.py`:
  - Environment and security configuration.
- `backend/api/views.py`:
  - Core DRF viewsets and queryset behavior.
- `backend/questionnaires/models.py`:
  - Questionnaire data model, versioning invariants, serializer.
- `backend/questionnaires/admin.py`:
  - Version clone-on-edit behavior and sortable admin setup.
- `backend/processes/models.py`:
  - Process parent object and process ordering.
- `frontend/src/router.tsx`:
  - Route definitions.
- `frontend/src/context/ApiManager.ts`:
  - API abstraction.

## Change Safety Checklist
- Before changing questionnaire selection logic:
  - confirm whether lookup must be by process slug, questionnaire id, or both.
  - validate latest-version behavior for `(process, name)`.
- Before changing ordering:
  - test Django admin changelist.
  - test sortable drag and reorder save.
  - test API list ordering and latest selection.
- Before changing Azure pipeline triggers:
  - preserve push-based CI for `feature/*`, `uat`, and `main` unless the workflow itself is being changed.
  - avoid reintroducing PR-triggered runs unless duplicate CI on feature branches is explicitly desired.
  - treat `pr: none` as the canonical setting for the current workflow.
- Before changing serializer contracts:
  - update frontend types and API manager calls in same change set.

## Contribution Guidance For Agents
- Prefer incremental, verifiable changes over broad rewrites.
- Do not run or generate migrations unless explicitly requested.
- Preserve historical data semantics: never collapse questionnaire versions.
- Keep owner/permission constraints intact when optimizing querysets.
- If third-party library behavior conflicts with project needs:
  - isolate root cause,
  - provide reproducible evidence,
  - prefer upstream fix or clear compatibility guardrails.
