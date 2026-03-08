# Copilot Instructions for DBCA Authorisations

## Purpose And Domain
- This system supports DBCA authorisation workflows, including Animal Ethics and Section 40/45 style application pathways.
- The platform is designed for versioned, process-driven forms where applicants submit applications that are backed by a questionnaire definition.
- A single authorisation process can include multiple questionnaire types (for example: New Application, Renewal) and each questionnaire type can have multiple versions over time.

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

## Integration Contracts

### Frontend <-> Backend
- REST API is the integration boundary.
- CSRF header behavior is configurable and can impact third-party components.
- Process and questionnaire contracts must stay in sync when changing lookup semantics.

### External Dependencies
- PostgreSQL behavior matters for DISTINCT and ORDER BY query design.
- `django-admin-sortable2` used for admin ordering UX; plugin limitations should be accounted for in model/admin configuration.

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

## Development Workflows

### Backend Commands
- Run dev server: `cd backend && poetry run python manage.py runserver`
- Run tests: `cd backend && poetry run python manage.py test`
- Run migrations: `cd backend && poetry run python manage.py migrate`
- Collect static: `cd backend && poetry run python manage.py collectstatic`

### Frontend Commands
- Run dev server: `cd frontend && npm run dev`
- Build: `cd frontend && npm run build`
- Lint: `cd frontend && npm run lint`

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
