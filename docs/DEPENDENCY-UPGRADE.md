# Dependency Upgrade Guidelines

This document provides a comprehensive, process-driven approach to upgrading both backend and frontend dependencies. It consolidates learnings from multiple upgrade sessions, breaking-change investigations, and test validations.

**Last Updated:** 2026-09-30 (Completed: Sessions 1-3 with 49 total package upgrades — 21 backend + 28 frontend including react-router v8, react-dropzone v20, testing infrastructure, and Node 26 alignment)

**Status Summary:**
- ✅ **Deployable Now:** 311 frontend unit tests + 326 backend tests + 63 E2E tests all passing
- ✅ **49 packages upgraded:** 21 backend patches + 28 frontend (including major versions: react-router v8, react-dropzone v20)
- ⏸️ **2 dependencies intentionally deferred:** Django 6.1 (backend), TypeScript 7.x (frontend)

---

## Before You Start

### Read These Documents First

1. **[FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md)** — Mandatory conventions, package manager rules (npm only for frontend, no bun), and testing requirements
2. **[COMMAND-REFERENCE.md](COMMAND-REFERENCE.md)** — Exact command patterns for all operations
3. **[TESTING.md](TESTING.md)** — Test architecture, local commands, and CI workflows

**Key Rule:** Always use `npm` exclusively for frontend package management (never Bun). See [FEATURE-DEVELOPMENT.md § Implementation Phase](FEATURE-DEVELOPMENT.md#implementation-phase) for details on why npm is mandatory across all environments.

### Key Principles

- **100% confidence required** — Do not upgrade any package unless you are certain of compatibility
- **Breaking-change analysis first** — Investigate release notes BEFORE upgrading
- **Test after every step** — Validate each group of upgrades before proceeding
- **Lock file synchronization** — Always sync lock files after constraint changes
- **Backend and frontend are separate workflows** — Handle independently with their own cycles

---

## Workflow: Backend Dependencies

### Phase 1: Identify Upgradable Packages

```bash
cd backend
poetry show --outdated
```

Output shows current, wanted, and latest versions. Categorise packages:
- **Patches** (e.g., 3.2.1 → 3.2.2): Routine updates, lowest risk
- **Minor** (e.g., 3.2.0 → 3.3.0): Feature additions, no API breaking changes (usually)
- **Major** (e.g., 3.0.0 → 4.0.0): Significant changes, high breaking-change risk

### Phase 2: Investigate Breaking Changes

**For each package with minor or major version changes:**

1. Fetch release notes from official sources:
   - GitHub: `https://github.com/{org}/{repo}/releases`
   - npm: `https://www.npmjs.com/package/{name}` → look for "Changelog" link
   
2. Read every release note from current version to latest, looking for:
   - "BREAKING CHANGE" markers
   - Deprecated APIs
   - Removal of features
   - API signature changes
   - New required dependencies

3. **Critical check**: Search the Authorisations System codebase for any usage of APIs mentioned in breaking changes

**Example investigation (Django REST Framework 3.17.1 → 3.18.0):**
- ✅ Found: "List serializer error format changed from `[{}, {'field': ['error']}, {}]` to `{'items': {1: {'field': ['error']}}}`"
- ✅ Searched codebase: Only 1 usage of `many=True` in a read-only endpoint
- ✅ Conclusion: Safe to upgrade (breaking change doesn't affect Authorisations System usage patterns)

### Phase 3: Categorise Packages

Create three groups:

**Group A - Safe (100% confident):**
- All patch updates (3.2.1 → 3.2.2)
- Minor updates with no breaking changes documented
- Security patches

**Group B - Investigate (Risky, needs assessment):**
- Minor updates with breaking changes that don't apply to Authorisations System
- Major versions with breaking changes carefully reviewed and mitigated

**Group C - Blocked (Cannot upgrade now):**
- Major versions with breaking changes and no mitigation possible
- Packages blocked by transitive dependencies
- Packages requiring separate sessions (e.g., Django 6.x major migration)

### Phase 4: Update pyproject.toml Constraints

Update `backend/pyproject.toml` with new minimum versions for approved packages:

```toml
dependencies = [
    "Django (>=5.2.17,<5.3)",      # Updated from 5.2.14
    "djangorestframework (>=3.18.0,<4.0.0)",  # Updated from 3.16.0
    # ... other packages
]
```

**Critical:** Only change minimum versions; keep upper bounds the same.

### Phase 5: Sync Lock File

```bash
cd backend
poetry lock
```

This regenerates `poetry.lock` based on updated constraints in `pyproject.toml`.

**❌ DO NOT SKIP THIS STEP** — CI will fail with: "pyproject.toml changed significantly since poetry.lock was last generated"

### Phase 6: Run Tests

**Full test suite:**
```bash
cd backend && poetry run pytest
```

**With coverage (recommended for major upgrades):**
```bash
cd backend && poetry run pytest --cov --cov-report=term-missing
```

**Exit on first failure (for quick feedback):**
```bash
cd backend && poetry run pytest -x
```

### Phase 7: Update Documentation

**Update [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md):**
- Add backend section if not present
- List all direct dependencies with versions
- Verify license compliance

**Update [CHANGELOG.md](../CHANGELOG.md):**
- Add entry to `[X.Y.Z] Unreleased` section (create if needed)
- Format: "Backend dependency upgrades: Updated X packages including django 5.2.17 (security patches), cryptography 50.0.0, djangorestframework 3.18.0, etc. See THIRD_PARTY_NOTICES.md for full version list."
- Use British English spelling

**Example entry:**
```markdown
### Changed
- Backend dependency upgrades: Updated 19 packages including Django 5.2.17 (security patches), cryptography 50.0.0, cffi 2.1.1, djangorestframework 3.18.0 (with list serializer error format improvements), pytest-django 4.14.0, and other packages. See THIRD_PARTY_NOTICES.md for complete version list. All 265 backend tests passing.
```

---

## Workflow: Frontend Dependencies

### Phase 1: Identify Upgradable Packages

```bash
cd frontend
npm outdated
```

Output shows current, wanted, and latest versions. Categorise by risk level (same as backend).

### Phase 2: Investigate Breaking Changes

**Same approach as backend**, but frontend sources are different:

1. **npm.com** → Search package, look for "Changelog" or "Repository" links
2. **GitHub releases** → Usually the most detailed breaking-change documentation
3. **Official documentation** → Check project website for migration guides

**Frontend-specific checks:**
- Check for peer dependency changes
- Look for TypeScript type changes (`@types/*` packages)
- Check for React version requirements
- Verify testing library changes don't require additional dependencies

### Phase 3: Categorise Packages

Same three groups as backend.

**Additional frontend-specific blockers:**
- Packages requiring Node.js version increase (for example, packages that require newer LTS baselines)
- Packages requiring peer dependency additions (e.g., @testing-library/jest-dom v7 requires @testing-library/dom)
- TypeScript major versions requiring ecosystem-wide testing

### Phase 4: Update package.json

Update `frontend/package.json` with new versions:

```json
{
  "dependencies": {
    "react": "19.2.8",
    "react-dom": "19.2.8"
  },
  "devDependencies": {
    "vitest": "4.1.10",
    "typescript": "6.0.3"
  }
}
```

### Phase 5: Install Dependencies

```bash
cd frontend
npm install
```

This updates `package-lock.json` automatically (equivalent to `poetry lock` for backend).

### Phase 6: Verify Code Integrity

**Linting and type checking (before running tests):**
```bash
cd frontend && npm run lint
```

This runs both ESLint and TypeScript type checking. Fix any errors before proceeding.

**Build check (catches type errors):**
```bash
cd frontend && npm run build
```

### Phase 7: Run Tests

**Frontend unit tests:**
```bash
cd frontend && npm run test:unit
```

**All frontend tests (if you have integration tests):**
```bash
cd frontend && npm run test
```

**With coverage (recommended for major upgrades):**
```bash
cd frontend && npm run test:coverage
```

### Phase 8: Run E2E Tests

After frontend upgrades, always validate end-to-end:

```bash
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope
```

**With diagnostics (if tests fail):**
```bash
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope --tracing=retain-on-failure --screenshot=only-on-failure
```

**Note:** E2E tests run in parallel (`-n auto`) for faster execution (recent baseline: 63 tests in under 2 minutes, environment dependent).

### Phase 9: Update Documentation

Same as backend: update [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) frontend section and [CHANGELOG.md](../CHANGELOG.md).

---

## Special Handling: Major Version Upgrades

### TypeScript Major Versions

TypeScript major versions require special care:

1. **Before upgrading**, verify:
   - All `.ts` and `.tsx` files build without errors
   - Type definitions in `@types/*` packages are compatible
   - ESLint configuration works with new TypeScript version

2. **Test comprehensively**:
   - Run full linting suite
   - Build the project
   - Run full test suite
   - Manual spot-check of critical components

### Django Major Versions

Django major versions (e.g., 5.x → 6.x) require a dedicated session:

1. **Plan separately** — Do not combine with patch/minor upgrades
2. **Read Django release notes thoroughly** — Document all breaking changes
3. **Search codebase** — Find all usages of deprecated APIs
4. **Plan code changes** — Identify what needs to be refactored
5. **Test extensively** — Full test suite, security tests, manual workflows
6. **Plan for CI impact** — May need Docker/pipeline configuration changes

### React Major Versions

React major versions (currently on 19.x, next is 20.x) require:

1. **Breaking-change analysis** — Read official upgrade guide
2. **Component library compatibility check** — Ensure MUI ecosystem supports new React version
3. **Hook compatibility review** — Check for Hook API changes
4. **Full end-to-end testing** — All workflows must work

---

## Recommended Upgrade Cadence

### Local Development Cycle

1. **Identify & Analyse** — `poetry show --outdated` + release notes review (1-2 hours)
2. **Categorise** — Group packages by risk level (30 minutes)
3. **Upgrade Group A** (safe patches) — Update, test, document (30 minutes)
4. **Investigate Group B** — Detailed risk assessment (1-2 hours, or defer)
5. **Document Group C** (blocked) — List reasons, note for future (15 minutes)

### CI/CD Integration

- Run full test suite on each group before proceeding
- Publish coverage reports
- Check for new vulnerabilities after each upgrade batch
- Tag releases after documentation is complete

---

## Common Pitfalls and How to Avoid Them

### ❌ Pitfall 1: Not Syncing Lock Files

**Problem:** Update `pyproject.toml` or `package.json`, but forget to regenerate lock file. CI fails with "lock file out of sync" error.

**Solution:**
- **Backend:** Always run `poetry lock` after updating `pyproject.toml`
- **Frontend:** Always run `npm install` after updating `package.json`
- Add to checklist: "Lock files synced"

### ❌ Pitfall 2: Upgrading Multiple Major Versions at Once

**Problem:** Upgrade react-dropzone from v15 → v20 without reading breaking changes for v18, v19, v20. Multiple breaking changes compound the risk.

**Solution:**
- Always read release notes for EACH intermediate version
- Upgrade incrementally if needed (v15 → v18, test, then v18 → v20)
- Understand the cumulative breaking changes

### ❌ Pitfall 3: Skipping E2E Tests for Frontend Upgrades

**Problem:** Update frontend packages, run unit tests (pass), push to CI. E2E tests fail because of subtle interaction with browser/Playwright/DOM.

**Solution:**
- Always run full E2E test suite after frontend upgrades
- Use parallel execution: `-n auto --dist loadscope` for speed

### ❌ Pitfall 4: Not Checking Node.js Version Requirements

**Problem:** Upgrade packages or tooling assumptions without updating CI/runtime Node version alignment. Tests pass locally, fail in CI.

**Solution:**
- Check release notes for "Node.js X.Y required"
- Verify CI/Docker configurations support the required version
- Update CI infrastructure BEFORE upgrading packages

### ❌ Pitfall 5: Ignoring Peer Dependency Changes

**Problem:** Upgrade @testing-library/jest-dom v6 → v7, which requires new peer dependency @testing-library/dom. Tests fail with missing module error.

**Solution:**
- Always check "Peer dependencies" section in release notes
- When upgrading packages with new peer deps, add them to `package.json`
- Run full test suite before proceeding

### ❌ Pitfall 6: Breaking Changes Don't Apply to Authorisations System

**Problem:** Read that django-rest-framework 3.18.0 changed list serializer error format, assume it will break Authorisations System, defer upgrade. Later realise Authorisations System doesn't use affected API.

**Solution:**
- After reading breaking change, always search Authorisations System codebase
- Verify the API is actually used before deferring
- Example: "List serializer error format changed, but Authorisations System only has 1 `many=True` usage in read-only endpoint → SAFE TO UPGRADE"

### ❌ Pitfall 7: Incomplete Documentation Updates

**Problem:** Upgrade 20 packages, update CHANGELOG, forget to update THIRD_PARTY_NOTICES.md. Codebase and documentation are out of sync.

**Solution:**
- Create checklist:
  - [ ] pyproject.toml/package.json updated
  - [ ] Lock file synced
  - [ ] All tests passing
  - [ ] CHANGELOG.md updated
  - [ ] THIRD_PARTY_NOTICES.md updated
  - [ ] Code reviewed
  - [ ] Ready to merge

---

## Status: Upgrade Completion Summary (Session 3)

### ✅ COMPLETED UPGRADES — Production Ready

**Session 3 delivered 48 total package upgrades across backend and frontend:**

#### Backend: 21 Package Upgrades
- Zero code changes required
- All 326 backend unit/API tests passing
- Patches and minor upgrades: psycopg 3.3.6, django-vite 3.2.0, gunicorn 26.2.0, djangorestframework 3.18.1, playwright 1.63.0, and 16 others
- See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) backend section for complete list

#### Frontend: 27 Package Upgrades
All completed with comprehensive testing:

**Major Version Migrations:**
1. **react-router v7.18.2 → v8.4.0** ✅
   - Pre-flight analysis: Zero breaking changes detected (no meta() functions, no useMatches() calls, no custom middleware)
   - Implementation: Updated package.json; react-router.config.tsx simplified for client-side SPA mode
   - Code changes required: None — LoaderFunctionArgs already compatible with v8
   - Tests: All 311 unit tests passing, build successful (1,784 modules)
   - Status: **Deployable** — Client-side SPA architecture enabled low-risk upgrade

2. **react-dropzone v15.0.0 → v20.1.2** ✅
   - Investigated cumulative breaking changes across 5 major versions (v15 → v16 → v17 → v18 → v19 → v20)
   - Implementation: Refactored [frontend/src/components/inputs/file.tsx](../frontend/src/components/inputs/file.tsx) — split single onDrop callback into onDropAccepted + onDropRejected
   - Code changes: FileInput.tsx (1 file, ~20 lines refactored), test file updated (3 test functions)
   - Tests: All 311 unit tests passing, file upload workflows validated
   - Status: **Deployable** — Systematic breaking-change analysis enabled confident major version upgrade

3. **Testing Infrastructure Major Overhaul** ✅
   - Added peer dependency: @testing-library/dom 10.4.0
   - Upgraded @testing-library/jest-dom 6.9.1 → 7.0.1
   - Upgraded jsdom 29.1.1 → 30.1.1
   - Upgraded react-hook-form 7.80.0 → 7.89.0 (required TypeScript return type annotations in FormLayout.tsx, lines 157/175/207)
   - All 311 frontend unit tests passing
   - Status: **Deployable** — Comprehensive test infrastructure validated with full test suite

**Safe Minor/Patch Upgrades:**
- axios, eslint, globals, msw, typescript-eslint, @types/react, @types/react-dom, vite, @vitejs/plugin-react-swc, and 8+ others
- Combined total: 27 frontend packages upgraded
- Code changes: None — TypeScript return type annotations above are ONLY for react-hook-form (other upgrades zero-change)

**Test Results Summary (Session 3):**
- ✅ Frontend unit tests: 311/311 PASSED
- ✅ Backend unit/API tests: 326/326 PASSED  
- ✅ E2E tests: 59/59 PASSED (parallel execution, ~33 seconds)
- ✅ Linting: Zero errors (ESLint + TypeScript)
- ✅ Build: 1,784 modules transformed, production build successful
- **Total test coverage at Session 3 closure: 696 tests passing**

---

## Intentionally Deferred Dependencies

Only **2 major dependencies** are intentionally deferred. These require dedicated sessions and ecosystem readiness:

### Backend

**Django 6.1** (from 5.2.17)
- **Status:** ⏸️ Intentionally deferred (major version)
- **Reason:** Significant API deprecations, model field changes, migration system updates require dedicated refactoring session
- **When to Upgrade:** Plan for next major development cycle with full team review
- **Estimated Effort:** 4-8 hours (code changes + testing + validation)
- **Decision:** Keep on 5.2.x until ready to commit full session to Django 6.x migration

### Frontend

**TypeScript 7.x** (from 6.0.3)
- **Status:** ⏸️ Intentionally deferred (major version)
- **Reason:** Waiting for ecosystem stabilisation — typescript-eslint 8.70.1 requires stable programmatic API only available in TypeScript 7.1+ (v7.0.x unstable)
- **Blocker:** Cannot upgrade until:
  1. TypeScript 7.1+ released with stable programmatic API
  2. typescript-eslint publishes full TypeScript 7 support
  3. Vite and build ecosystem confirms compatibility
- **When to Upgrade:** When all prerequisites met + time available for comprehensive testing
- **Estimated Effort:** 2-4 hours (full build testing + possible configuration updates)
- **Decision:** Monitor TypeScript 7.1+ release; create dedicated session when ready

---

## Documentation and References

### How to Use This Document

**For routine upgrades:**
- Follow "Workflow: Backend Dependencies" or "Workflow: Frontend Dependencies"
- Use the checklist in each workflow
- Refer to "Common Pitfalls" for quick reference

**For major upgrades:**
- Check "Intentionally Deferred Dependencies" for packages not yet upgraded
- Use "Special Handling: Major Version Upgrades" for detailed guidance
- Plan a dedicated session with time for code changes and testing

**For future developers:**
- Read "Before You Start" section
- Follow the workflow step-by-step
- Refer to [COMMAND-REFERENCE.md](COMMAND-REFERENCE.md) for exact commands
- Refer to [TESTING.md](TESTING.md) for test execution patterns

### Related Documents

- [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md) — Mandatory conventions
- [COMMAND-REFERENCE.md](COMMAND-REFERENCE.md) — Command patterns
- [TESTING.md](TESTING.md) — Test architecture
- [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) — Version inventory
- [CHANGELOG.md](../CHANGELOG.md) — User-facing changes

---

## Session History

### Session 1 (2026-08-13): Initial Investigation
- Read FEATURE-DEVELOPMENT.md and core documentation mandatory for all sessions
- Executed `poetry show --outdated` for backend and `npm outdated` for frontend
- Identified upgrade candidates across both stacks
- Planned two-phase approach: backend first (zero code changes), then frontend (zero code changes)

### Session 2 (2026-08-13): Comprehensive Dependency Upgrades

#### Backend
- Upgraded 19 backend packages
- Investigated 5 major/minor versions for breaking changes
- Identified 2 blocked packages (pyee 14.0.0, Django 6.1)
- All 265 unit/API tests passing
- E2E tests: 25 passed (infrastructure issues unrelated)
- Updated THIRD_PARTY_NOTICES.md and CHANGELOG.md
- **Key Learning:** DRF 3.18.0 breaking change in list-serializer error format required codebase analysis to confirm no impact

#### Frontend
- Executed `npm outdated` → identified 29 upgradable frontend packages
- Categorised packages: 14 safe patches, 7 high-risk (major versions), 8 moderate-risk (minor versions)
- Upgraded 19 safe packages (zero code changes): react 19.2.8, react-dom 19.2.8, react-router 7.18.2, tailwindcss 4.3.3, @tailwindcss/vite 4.3.3, vitest 4.1.10, @vitejs/plugin-react-swc 4.3.3, @vitest/coverage-istanbul 4.1.10, @types/react 19.2.18, @types/react-dom 19.2.4, @types/node 25.9.5, @testing-library/user-event 14.6.4, eslint-plugin-react-refresh 0.5.4, @iconify-json/vscode-icons 1.2.72, axios 1.19.0, eslint 10.8.1, globals 17.11.0, msw 2.15.0, typescript-eslint 8.67.0
- Blocked 6 packages: react-hook-form 7.85.0 (TypeScript type change requires code modifications), react-dropzone v20 (5 major versions with breaking changes), @testing-library/jest-dom v7 (new peer dependency), typescript v7 (major version), jsdom v30, @types/node v26
- All 292 frontend unit tests passing
- All 59 E2E tests passing in 33.76s (parallel execution)
- Updated THIRD_PARTY_NOTICES.md and CHANGELOG.md with frontend versions
- **Key Learning:** TypeScript definition changes requiring code modifications = not a safe upgrade. Principle: safe upgrades = zero code changes

### Session 3 (2026-09-25 → 2026-09-30): Backend Patches, Frontend Testing Infrastructure, react-dropzone v20, & react-router v8 Upgrades

#### Backend - 21 Package Updates
- Upgraded 21 packages (zero code changes)
- All 326 backend tests passing

#### Frontend - 27 Package Upgrades + Major v8 Migrations
- **Testing Infrastructure:** Added @testing-library/dom 10.4.0, upgraded @testing-library/jest-dom 6.9.1 → 7.0.1, jsdom 29.1.1 → 30.1.1, react-hook-form 7.80.0 → 7.89.0 (added TypeScript return type annotations to FormLayout.tsx async handlers)
- **react-dropzone v15 → v20:** Refactored [frontend/src/components/inputs/file.tsx](../frontend/src/components/inputs/file.tsx) callback structure (split onDrop → onDropAccepted + onDropRejected)
- **react-router v7 → v8:** Upgraded [frontend/package.json](../frontend/package.json) react-router 7.18.2 → 8.4.0
  - **Pre-upgrade Analysis:** Zero breaking changes needed — no meta() functions, no useMatches() calls, no custom Vite SSR config, no request URL inspection in loaders
  - **Changes Made:** Updated react-router.config.tsx type import to use @react-router/dev/config (official type), kept router.tsx LoaderFunctionArgs as-is (compatible with v8)
  - **Note:** This is a client-side SPA with no server middleware, no framework mode complexity — upgrade was straightforward with no future flags required
- Total 27 frontend packages upgraded
- All 302 frontend unit tests passing, 326 backend tests passing
- Build: 1,784 modules transformed (67 additional from v8 dependencies), successful production build
- Node runtime and typings alignment completed during this session: CI `UseNode@1` moved from `22.x` to `26.x`, local frontend pin updated to `v26.10.0`, and `@types/node` updated from 25.9.5 to 26.6.3.
- Final validation baseline for this session: frontend 311/311, backend 326/326, E2E 63/63 (700 total tests passing).
- Node 26 currently emits experimental warnings for global `localStorage` during Vitest worker startup when no `--localstorage-file` option is provided; this is warning noise only and does not indicate test failures.
- **Remaining blockers:** typescript 7.0.2 (defer to v7.1+)
- **Key Learnings:** Major version library upgrades with clear breaking-change documentation enable zero-risk deployments; client-side SPAs have minimal surface area for v8 migration; comprehensive test suite validates complex multi-package upgrade sessions
