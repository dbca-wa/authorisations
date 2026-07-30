# Feature Development Checklist

This document defines the **mandatory guidelines and checklist for all feature development and bug fixes**. AI agents and developers must follow these practices on every session unless explicitly told otherwise by the project owner.

---

## Before You Start

### 1. Understand the architecture and conventions

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the data model, terminology, and design decisions.
- Review [BACKEND-CONVENTIONS.md](BACKEND-CONVENTIONS.md) for backend patterns, security rules, and ordering constraints.
- Review [FRONTEND-CONVENTIONS.md](FRONTEND-CONVENTIONS.md) for React, TypeScript, and component guidelines.
- Check [FRONTEND-API-FLOWS.md](FRONTEND-API-FLOWS.md) for user journeys and authentication context.
- Check [STATUS-WORKFLOW.md](STATUS-WORKFLOW.md) for application status and business transitions.

### 2. Determine scope and layers

- Decide whether your feature affects frontend, backend, or both.
- Identify if new API endpoints or serializer changes are needed.
- Plan test coverage: unit, API, security, integration, and/or E2E.
- Identify if documentation updates are needed (README, guides, or architecture docs).

---

## Implementation Phase

### 1. Package managers — mandatory rule

**Frontend package management (mandatory across all environments):**
- Use `npm` exclusively for **all** frontend package management: local development, dependency installation, linting, testing, building, and production deployments
- `npm` is the only supported package manager; all CI/Docker builds and development workflows use npm
- This ensures identical dependency resolution and versions across all environments: development, CI, UAT, and production

**Why not Bun?**
While Bun offers performance improvements, it introduces critical compatibility risks:
- **Dependency resolution differences**: Bun's algorithm resolves optional and peer dependencies differently than npm, resulting in mismatched versions across environments (e.g., yaml@1.10.2 vs yaml@2.9.0).
- **Incompatible lock file formats**: Bun's lock file (`bun.lock`) cannot be reliably converted to npm's format; attempting to do so produces different dependency trees.
- **Production incompatibility**: Most production environments, container registries, and audit tools expect npm lock files; Bun is not suitable for production.
- **Maintenance burden**: Supporting multiple package managers exponentially increases debugging complexity and CI/CD fragility.

**Workflow when adding dependencies:**
1. Use `npm install package-name` to add a package (updates `package-lock.json`)
2. Commit both `package.json` and `package-lock.json` to git
3. CI and Docker builds use `npm ci` for reproducible installs from the committed lock file
4. Result: guaranteed identical versions everywhere, no version drift, predictable builds

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

### 3. Minimalist Implementation Principles

**Core principle: Simple is better, less is more.** Push logic down to where it belongs, avoid layers of indirection, and let components be self-sufficient.

#### Anti-patterns to avoid

**❌ Don't:** Orchestrate everything from a parent component
- ❌ Parent manages multiple refs, metadata maps, and callbacks for child components
- ❌ Parent passes callbacks to children just to track state that children could own
- ❌ Parent maintains ref collections and coordinates all state changes
- ❌ Each decision wrapped in checks of checks: optional parameters with defensive ternary chains

Example of over-orchestration:
```typescript
// ❌ Too many layers
const Parent = () => {
  const dataMap = useRef<Record<string, Data>>({});
  const refMap = useRef<Record<string, HTMLDivElement | null>>({});
  const metaMap = useRef<Record<string, Meta>>({});
  
  useEffect(() => {
    // Sync all three maps, handle callbacks, coordinate scroll...
  }, [deps]);
  
  return (
    <Child onRef={(ref) => { refMap.current[key] = ref; }} 
           onMeta={(meta) => { metaMap.current[key] = meta; }}
           data={dataMap.current[key]} />
  );
};
```

**✅ Do:** Let each component own its concerns
- ✅ Child components check their own conditions and manage their own state
- ✅ Props are the only communication boundary (input data, output callbacks for user actions)
- ✅ Each component has a clear, singular responsibility
- ✅ No defensive checks unless absolutely necessary; default to sensible values

Example of minimal implementation:
```typescript
// ✅ Simple and clean
const Child = ({ data }) => {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // Child checks if data applies to it
    if (shouldProcessData(data)) {
      setState(computedValue);
    }
  }, [data]);
  
  return <div>...</div>;
};

const Parent = ({ items }) => {
  return items.map(item => <Child key={item.id} data={item} />);
};
```

#### Practical guidelines

1. **Start with the simplest possible implementation that solves the problem.**
   - Don't add infrastructure "just in case"
   - Don't create abstractions before you need them
   - Don't create ref collections or metadata maps unless truly unavoidable

2. **If you find yourself creating multiple refs/maps to coordinate state, stop and ask:**
   - Could the child component own this state instead?
   - Could this logic live in a single component without orchestration?
   - Is the complexity justified by the feature, or am I over-engineering?

3. **Dependency arrays and effect scoping:**
   - Effects should depend on what they actually use (not proxy values)
   - If you're listening to `window.location.hash` in an effect, either:
     - Include it in dependencies (with proper handling), OR
     - Listen to `hashchange` events explicitly (clearer intent)
   - Don't silence eslint warnings (`// eslint-disable`) to hide the real issue

4. **Props and communication:**
   - Pass only what the component needs (not "just in case" props)
   - Use callbacks for user actions, not for internal state sync
   - Avoid optional props with defensive defaults; require sensible values or compute them at the boundary

5. **When to refactor:**
   - Refactor when code is duplicated across multiple components
   - Refactor when a single responsibility becomes too large (>200 lines)
   - Don't refactor prematurely or "improve" working code—the best code is the simplest code that works

#### Trade-offs

Minimalist implementation may mean:
- Features that work for 95% of use cases rather than 100% (edge cases handled in future iterations)
- Components that are "good enough" rather than maximally reusable
- Accepting that some features have reasonable limitations (document them)

This is intentional. Overbuilding creates maintenance debt and obscures real logic under layers of indirection.

### 4. Code quality — syntax, types, and linting

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
1. Check TypeScript and linting:
   ```bash
   cd frontend && npm run lint
   ```

2. Fix issues automatically:
   ```bash
   cd frontend && npm run lint -- --fix
   ```

3. Build check (catches type errors):
   ```bash
   cd frontend && npm run build
   ```

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
**E2E required if workflow is mission-critical (e.g., application submission, review handoff).

### Test locations and commands

#### Backend tests

**All backend tests use** `cd backend && poetry run pytest` **from the backend directory.**

Structure:
- All application tests: `backend/{app}/tests/test_*.py` (e.g., `test_models.py`, `test_serialisers.py`, `test_views_security.py`)
- API endpoint tests: `backend/api/tests/test_*.py`
- Management command tests: `backend/{app}/tests/test_management_commands.py`
- E2E tests: `backend/e2e/tests/test_*.py`

**Test file naming convention:**
- `test_models.py` — Unit and model tests
- `test_serialisers.py` — Serialiser validation tests
- `test_views_security.py` — Non-API view access control (marked with `@pytest.mark.security`)
- `test_api_endpoint_security.py` — API endpoint security and authorization (marked with `@pytest.mark.security`)
- `test_forms.py` — Form field and form validation tests
- `test_prince.py` — Utility/command wrapper tests

**Security test organization:** Security tests are **co-located with application tests** in the `tests/` directory (not separated into a special folder). Use `@pytest.mark.security` for logical grouping. This enables:
1. Unified test discovery via `pytest -m security` or `pytest -m "security and api"`
2. Clear file naming (`*_security.py`) makes purpose obvious
3. Everything organized under `tests/` for consistent structure
4. Tests live near the code they verify

Commands:
```bash
cd backend
# All backend tests
poetry run pytest

# Specific app
poetry run pytest applications -q

# Specific test file
poetry run pytest applications/tests/test_models.py -v

# Security tests only
poetry run pytest -m security -v

# E2E tests only
poetry run pytest e2e/tests -v

# With coverage
poetry run pytest -n auto --cov --cov-report=term-missing --cov-report=html
```

#### Frontend tests

**For all contexts (development, CI, production)**, use `npm` with the committed `package-lock.json`.

Structure:
- Component unit tests: `frontend/src/test/unit/components/**/*.test.tsx`
- Context tests: `frontend/src/test/unit/context/**/*.test.tsx`
- Utility tests: `frontend/src/test/unit/**/*.test.ts`

Commands:
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

- Use E2E for mission-critical user journeys (e.g., application submission, review workflow).
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

- **STATUS-WORKFLOW.md** lifecycle of an application within the Authorisations system.
- **ARCHITECTURE.md**: major data model changes, new entities, or core design decisions.
- **FRONTEND-API-FLOWS.md**: new routes, new authentication/permission rules, new user workflows.
- **STATUS-WORKFLOW.md**: changes to application statuses or transition logic.
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
- **Critical**: Never modify past release notes; only add entries to the `Unreleased` section. Changing historical entries corrupts the release timeline and audit trail.

### Example CHANGELOG entries

✓ Good:
```
- Added attachments dialog for technical officers to view and download application files from the review queue.
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
  - Frontend: `cd frontend && npm run test:coverage`
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

### Frontend

```bash
cd frontend

# Dev server
npm run dev

# Build
npm run build

# Lint and type check
npm run lint

# Tests
npm run test:unit

# Coverage
npm run test:coverage
```

---

**See [README.md](README.md) for the documentation index.**
