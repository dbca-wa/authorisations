# Architecture

This document describes the data model, terminology, and business logic behind the Authorisations system.

## Purpose and domain

This system supports DBCA authorisation workflows, including Animal Ethics and Section 40/45 style application pathways. The platform is designed for versioned, process-driven forms where applicants submit applications that are backed by a questionnaire definition. A single authorisation process can include multiple questionnaire types (for example: New Application, Renewal) and each questionnaire type can have multiple versions over time.

## Technical stack

### Backend
- Django 5.2, Django REST Framework, PostgreSQL
- Modular apps under `backend/`: `applications`, `questionnaires`, `processes`, `api`, `users`

### Frontend
- React + TypeScript + Vite + MUI + Tailwind
- Routing in `frontend/src/router.tsx`
- API access abstraction in `frontend/src/context/ApiManager.ts`

### Deployment/runtime
- Docker supported
- Backend startup orchestration in `backend/entrypoint.sh` (collectstatic, migrate, gunicorn)
- Kubernetes kustomize configuration under `kustomize/`

## Current canonical terminology

### AuthorisationProcess
- Parent domain object that groups related questionnaires under a business process
- Owns stable process identity via `slug` and display ordering via `sort_order`

### Questionnaire
- Versioned schema/content definition used to build application forms
- Belongs to one `AuthorisationProcess`
- Has a business `name` (questionnaire kind within the process), `version`, and `sort_order`

### Application
- User-owned submitted/draft record tied to one specific questionnaire version

### ApplicationAttachment
- File metadata linked to an application, soft deletable

### Terminology migration notes
- Historical/legacy mental model treated questionnaire `slug` as top-level identity
- Current model treats process `slug` as process identity and questionnaire `id` as concrete questionnaire identity
- For stable evolution, prefer explicit questionnaire identity (`id`) in create/update flows where ambiguity exists

## Data relationships

### Core relationship graph
- One `AuthorisationProcess` has many `Questionnaire` records
- One `Questionnaire` belongs to exactly one `AuthorisationProcess`
- One `Questionnaire` can have many `Application` records
- One `Application` belongs to exactly one `Questionnaire` and one owner (`users.User`)
- One `Application` has many `ApplicationAttachment` records
- One `ApplicationAttachment` belongs to exactly one `Application`

### Key questionnaire invariants
- Questionnaire uniqueness/versioning invariant: Unique constraint includes `(process, name, version DESC expression)` by name `qnaire_unique_process_name_version_desc`
- Operational meaning: For each `(process, name)`, there may be multiple rows by version. "Latest" is determined by highest `version` for that pair

## Business logic behind technical structure

### Why AuthorisationProcess exists
- Business users need a process-level grouping independent of questionnaire revisions
- Process metadata (name, description, image, sort order, slug) should remain stable while questionnaires evolve
- Process-level grouping improves applicant UX by presenting clear process categories before selecting questionnaire type

### Why Questionnaire is versioned
- Regulatory/business forms evolve over time and old applications must remain linked to the exact questionnaire version they were created from
- Version cloning in admin preserves immutable history while allowing updates to produce a new latest version
- Latest version selection is a read concern; historical version retention is a compliance/audit concern

### Why distinct latest selection is explicit
- Requirement: list one active/latest questionnaire per `(process, questionnaire name)`
- PostgreSQL `DISTINCT ON` semantics enforce strict alignment between `DISTINCT ON` columns and initial `ORDER BY` columns
- Therefore latest-selection ordering and final display ordering are often separate concerns and may require a two-step queryset pattern

### Why ordering is managed carefully
- `sort_order` on process and questionnaire encodes curated display sequence
- Third-party admin drag-and-drop integration (`django-admin-sortable2`) expects the primary sortable field to be a concrete local model attribute
- Relation traversals in model `Meta.ordering` (for example `process__sort_order`) may be valid in Django ORM, but can break plugin internals that do `getattr(obj, field_name)`

## Integration contracts

### Frontend <-> Backend
- REST API is the integration boundary
- CSRF header behaviour is configurable and can impact third-party components
- Process and questionnaire contracts must stay in sync when changing lookup semantics

### External dependencies
- PostgreSQL behaviour matters for DISTINCT and ORDER BY query design
- `django-admin-sortable2` used for admin ordering UX; plugin limitations should be accounted for in model/admin configuration

## PDF icon CSS build contract

### Why pdf-icons.css exists
- The application PDF renders file-type icons that must match frontend icon mapping logic
- Prince renders the PDF without relying on runtime HTTP fetches for this icon stylesheet
- A dedicated Vite entry builds a stable output file named `pdf-icons.css` so Django staticfiles can always find it by that exact name

### How it is generated
- Source entry is `frontend/src/pdf-icons.css`
- Vite includes a dedicated build input named `pdf-icons` and emits hash-free `pdf-icons.css`
- Tailwind v4 scans explicit sources declared in `pdf-icons.css`:
  - `backend/applications/models.py` (icon class mapping values)
  - `backend/templates/application-pdf-template.html` (base icon class usage)
- During PDF context building, backend code loads `pdf-icons.css` via Django staticfiles finder and inlines it into the template

### Docker build path requirement (Critical)
- `frontend/src/pdf-icons.css` uses relative `@source` paths that assume:
  - frontend source is available at `/tmp/frontend`
  - backend source is available at `/tmp/backend`
- Therefore Docker builds that run `npm run build` for frontend must copy both source trees into those temporary locations before the build step
- If either source path is missing, Tailwind cannot resolve icon class sources and the generated `pdf-icons.css` will be incomplete or incorrect

### Safe change checklist
- If moving directories or changing Docker stages, preserve the relative source relationship used by `pdf-icons.css`
- If adding new attachment file types, update `_EXTENSION_TO_ICON_CLASS` in `backend/applications/models.py` and rebuild frontend assets
- After build changes, verify that output contains `pdf-icons.css` and that generated PDFs still show correct file-type icons

---

**See [README.md](README.md) for the documentation index.**
