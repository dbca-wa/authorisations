# Backend Conventions

Development patterns, rules, and best practices for the backend codebase.

## API layer

- DRF viewsets are in `backend/api/views.py`
- Serializers are primarily in app `serialisers.py`; questionnaire serializer intentionally sits with model due to schema import/circular dependency constraints
- Prefer `select_related` on known foreign-key paths for list/retrieve endpoints to avoid N+1 behaviour

## Security and ownership

- Application and attachment querysets must always enforce owner scoping
- Attachment deletions are soft-delete and must include ownership checks
- CSRF behaviour includes project-specific configuration and has known interactions with third-party admin endpoints

### Read access vs write access (`has_access` vs owner check)

- `Application.has_access(user)` grants **read** access. Two principals qualify:
  1. The application owner
  2. Any authenticated user whose groups intersect the process's `reviewer_groups` (technical officers / assessors)
- `has_access` must **not** be used as the guard for write/mutation paths
  - `resume_application` (the interactive form URL) uses an explicit `application.owner == request.user` check so that reviewers cannot open and modify someone else's application through the form
  - `download_application` and `download_attachment` correctly use `has_access` because those are read-only operations
- Whenever adding a new endpoint or view that touches application data, decide explicitly: is this a read path (use `has_access`) or a write/owner-only path (use explicit `owner == user` check)?

## Ordering rules

- Keep model `Meta.ordering` simple and local-field based when sortable admin integrations are used
- Use explicit queryset ordering in API/admin where relation-based ordering is needed
- Do not assume one ordering expression can satisfy both:
  - latest row selection by grouping key
  - final display order

## Admin behaviour

### Questionnaire admin intent
- Admin edits clone on change:
  - Increment version, set `pk=None`, persist as new row
- Read-only fields protect immutable dimensions for existing versions
- Add/change action buttons are intentionally simplified for workflow control

### django-admin-sortable2 constraints
- First ordering field used by sortable mixin must be writable concrete field on the model (for this project: `sort_order`)
- Do not make sortable admin depend on relation traversal ordering key
- If relation-based display ordering is needed, use queryset-level `.order_by(...)` for read paths, not sortable field identity

## Known gotchas

### Distinct On (PostgreSQL)
- Error pattern: `SELECT DISTINCT ON expressions must match initial ORDER BY expressions`
- Root cause: order prefix mismatch against distinct fields
- Safe pattern for latest-per-group:
  - first select by `order_by(group_fields..., -version).distinct(group_fields...)`
  - then apply final display order in outer queryset if needed

### Relation in Meta.ordering
- Django supports relation ordering in many ORM contexts
- Some admin/plugin internals may treat ordering key as direct object attribute, causing runtime attribute errors
- Practical recommendation in this codebase:
  - keep `Meta.ordering` local/simple
  - apply relation ordering explicitly in querysets where required

### Sortable2 compatibility
- Library internals rely on writable field operations (`getattr/setattr/bulk_update`) against the default sortable field
- Relation traversals are not writable sortable fields

### Questionnaire sort order normalisation command
- Command: `normalise_questionnaire_sort_order`
- Purpose:
  - Rebuild `Questionnaire.sort_order` values globally with a visible/latest-first policy
  - Recover from corrupted ordering states (for example many rows at `0`, gaps, duplicates, negative values)
- Behaviour:
  - Determines current visible questionnaire order from latest versions by existing `sort_order`
  - Reassigns latest versions to contiguous visible ranks `1..N` in that preserved global order
  - Sets all historical (non-latest) versions to `0` so they do not interfere with visible ordering
  - Updates only rows that need change
  - Safe and idempotent: repeated runs converge to the same result and make no further updates once normalised
- Operational note:
  - Prefer this command over `manage.py reorder questionnaires.Questionnaire` for this model, because `reorder` uses `Meta.ordering[0]` and may target non-sort fields

## Development workflows

### Backend commands
- Run dev server: `cd backend && poetry run python manage.py runserver`
- Run tests: `cd backend && poetry run python manage.py test`
- Run migrations: `cd backend && poetry run python manage.py migrate`
- Collect static: `cd backend && poetry run python manage.py collectstatic`
- Normalise questionnaire sort order globally:
  - `cd backend && poetry run python manage.py normalise_questionnaire_sort_order`
  - Dry-run mode: `cd backend && poetry run python manage.py normalise_questionnaire_sort_order --dry-run`

## CI/CD pipeline policy

- Azure Pipelines YAML is hosted in GitHub, so CI and PR trigger behaviour is controlled in `azure-pipelines.yml` rather than Azure Repos branch policies
- CI should run on direct pushes to `main`, `uat`, and `feature/*` branches
- Pull request triggered pipeline runs are intentionally disabled with `pr: none` to avoid duplicate runs when a feature branch already has push-based CI
- Feature branch workflow expectation:
  - push to `feature/*` runs the full test pipeline once
  - opening or updating a PR from that feature branch should not start a second PR-validation pipeline
- The Docker build and push steps may still keep a `Build.Reason != PullRequest` condition as a defensive guard, but PR suppression should be enforced primarily by `pr: none`
- When Docker build arguments are required (for example env used during `collectstatic`), prefer `Docker@2 build` then `Docker@2 push` in one job instead of `buildAndPush`
- For script steps, do not use environment variable keys beginning with `SECRET_`; use `DJANGO_SECRET_KEY` and map to Django settings accordingly
- For code coverage, publish once from a dedicated aggregation job rather than publishing separately from backend and frontend jobs

## CI test environment requirements

- Backend pytest uses `config.test_settings`, which imports `config.settings` first
- Import-time settings evaluation still requires baseline env vars before test overrides apply
- Safe pattern for this codebase in CI backend test job:
  - set `DATABASE_URL` to SQLite (`sqlite:///:memory:`)
  - pass `DJANGO_SECRET_KEY`
  - set `LOCAL_MEDIA_STORAGE='true'`
  - set `PRIVATE_MEDIA_ROOT` to a writable temp path (for example `/tmp/private-media`)

## Known Azure Pipelines gotchas

### Secret prefix filtering
- Azure Pipelines can filter script environment variable names that begin with reserved prefixes, including `secret` (case-insensitive)
- Practical impact observed in this project:
  - `SECRET_KEY` in a script `env:` block arrives empty in bash even when the source pipeline variable is set
  - `DJANGO_SECRET_KEY` in the same `env:` block arrives correctly
- Safe pattern for this codebase:
  - Do not map script env keys that begin with `SECRET_`
  - Map `DJANGO_SECRET_KEY` in pipeline YAML and read it first in Django settings, with `SECRET_KEY` fallback for local compatibility

### Docker@2 buildAndPush and build arguments
- In this project, `Docker@2` with `command: buildAndPush` did not reliably pass `arguments` (for example `--build-arg LOCAL_MEDIA_STORAGE=...`) to the Docker build
- Symptom:
  - Pipeline debug step shows `LOCAL_MEDIA_STORAGE` is set
  - Dockerfile step before `collectstatic` sees `LOCAL_MEDIA_STORAGE(raw)=''`
- Safe pattern for this codebase:
  - Use `Docker@2` `command: build` with `arguments`, followed by `Docker@2` `command: push` in the same job
  - Keep build and push in the same job so the local image remains available for push

### Docker image availability across jobs
- Docker images built on Microsoft-hosted agents are not shared across jobs/stages
- Symptom:
  - Push job logs `An image does not exist locally with the tag ...` when build and push are split across different jobs/stages
- Safe pattern for this codebase:
  - Keep Docker build and Docker push in the same job
  - If stages must be split, explicitly transfer image artifacts (`docker save` / `docker load`)

### Node task migration gotcha (UseNode@1)
- `NodeTool@0` is deprecated and should be replaced with `UseNode@1`
- `UseNode@1` expects input key `version` (not `versionSpec`)
- Symptom when misconfigured:
  - Task label says Node 22, but agent installs default Node 10.x
  - Frontend `npm ci` fails with dependency-resolution/runtime errors
- Safe pattern for this codebase:
  - Use:
    - task: `UseNode@1`
    - inputs: `version: '22.x'`

### Coverage publish overwrite behaviour
- Publishing backend and frontend coverage independently can lead Azure DevOps Code Coverage tab to show only the last published dataset
- Symptom:
  - Coverage tab shows only frontend (`.tsx`) or only backend files depending on publish order
- Safe pattern for this codebase:
  - Publish raw coverage XML from each test job as pipeline artifacts
  - Add a dedicated downstream `Coverage` job that downloads both artifacts and runs a single `PublishCodeCoverageResults@2` step

## Change safety checklist

- Before changing questionnaire selection logic:
  - confirm whether lookup must be by process slug, questionnaire id, or both
  - validate latest-version behaviour for `(process, name)`
- Before changing ordering:
  - test Django admin changelist
  - test sortable drag and reorder save
  - test API list ordering and latest selection
- Before changing Azure pipeline triggers:
  - preserve push-based CI for `feature/*`, `uat`, and `main` unless the workflow itself is being changed
  - avoid reintroducing PR-triggered runs unless duplicate CI on feature branches is explicitly desired
  - treat `pr: none` as the canonical setting for the current workflow
- Before changing serializer contracts:
  - update frontend types and API manager calls in same change set

---

**See [README.md](README.md) for the documentation index.**
