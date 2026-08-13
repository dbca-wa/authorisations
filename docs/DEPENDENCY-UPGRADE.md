# Dependency Upgrade Guidelines

This document provides a comprehensive, process-driven approach to upgrading both backend and frontend dependencies. It consolidates learnings from multiple upgrade sessions, breaking-change investigations, and test validations.

**Last Updated:** 2026-08-13 (Session 1: Initial Investigation, Session 2: Comprehensive Upgrades)

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
- Packages requiring Node.js version increase (e.g., react-dropzone v20 requires Node 22+)
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

**Note:** E2E tests run in parallel (`-n auto`) for faster execution (~34 seconds for 59 tests vs. 83 seconds sequential).

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

**Problem:** Upgrade packages that require Node 22+, but CI still runs on Node 20. Tests pass locally, fail in CI.

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

## Status: Frontend Moderate-Risk Packages (Session 2)

### ✅ Upgraded (5 packages)

After careful release-note analysis and codebase testing, the following 5 minor-version packages were verified safe and upgraded with **zero code changes required**:

| Package | Version Range | Status | Key Finding |
|---------|---------------|--------|------------|
| **axios** | 1.18.1 → 1.19.0 | ✅ SAFE | Security hardening only; no API changes |
| **eslint** | 10.6.0 → 10.8.1 | ✅ SAFE | Features and bug fixes; no breaking changes |
| **globals** | 17.7.0 → 17.11.0 | ✅ SAFE | Read-only data updates (ESLint globals); no impact |
| **msw** | 2.14.6 → 2.15.0 | ✅ SAFE | Optional new SSE handler (finalize callback); no API changes |
| **typescript-eslint** | 8.62.1 → 8.67.0 | ⚠️ CAUTION | 2 rule deprecations (no-restricted-imports, no-loop-func) — warnings only in v8; plan migration before v9 |

**Code Changes Required:** NONE — All 5 packages upgraded and fully tested with zero codebase modifications.

**Test Results:**
- ✅ ESLint: Passed
- ✅ TypeScript: Passed
- ✅ Frontend unit tests: 292/292 PASSED
- ✅ E2E tests: 59/59 PASSED (33.76s)

### ⛔ Blocked: react-hook-form 7.85.0

**Status:** BLOCKED — Requires Code Changes

**Version Range:** 7.80.0 → 7.85.0

**Blocker:** TypeScript type definition changes in handleSubmit return type require explicit type annotations on async submit handlers (onValid and onInvalid). This violates the core principle: **safe upgrades require zero code modifications**.

**Breaking Change:** handleSubmit returns `Promise<unknown>` instead of `Promise<void>`, requiring explicit return type annotations or type assertions.

**Codebase Impact:** FormLayout.tsx, lines 157–207 require type annotation additions to onValid and onInvalid async handlers.

**Decision:** Defer upgrade until react-hook-form resolves TypeScript compatibility without requiring code changes. Current version 7.80.0 is fully functional; upgrade is not critical.

**When Ready:** Monitor react-hook-form releases for v7.86+ that may resolve TypeScript strictness issues without code impact.

**Estimated Effort:** If upgraded: 30 minutes (type annotation additions in FormLayout.tsx and possibly other form-related files).

### ⏳ Remaining Moderate-Risk Packages (2 packages)

These require investigation but have not been prioritised:

| Package | Current | Latest | Risk | Notes |
|---------|---------|--------|------|-------|
| @types/eslint | 9.6.1 | (check npm) | TBD | Part of ESLint ecosystem update chain |
| (other 1 package TBD) | (check npm outdated) | (check npm) | TBD | Requires release-note review |

**Action:** Run `npm outdated` to get latest versions and prioritise based on release notes.

---

## Pending Upgrades with Breaking Changes

### Blocked: Requires Dedicated Session

These packages have breaking changes or infrastructure requirements that make them unsuitable for routine upgrade sessions. Plan a dedicated session when ready.

#### Backend

**Django 6.1** (from 5.2.17)
- **Status:** ⏸️ Deferred (major version)
- **Breaking Changes:** Multiple API deprecations, model field changes, migration system updates
- **Decision:** Requires separate focused session with dedicated testing
- **When Ready:** Plan for next major cycle with full team review
- **Estimated Effort:** 4-8 hours (code changes + testing + validation)

#### Frontend

**react-router 8.x** (from 7.18.2)
- **Status:** ⏸️ Intentionally deferred
- **Reason:** FEATURE-DEVELOPMENT.md explicitly states "intentionally on 7.x to avoid major 8.x breaking changes"
- **Breaking Changes:** Route API, loader patterns, error handling
- **Decision:** Keep on 7.x until 8.x stabilises or project is ready for major refactor
- **When Ready:** After stabilisation period, plan upgrade with route refactoring

**react-dropzone 20.x** (from 15.0.0)
- **Status:** ⛔ Blocked (5 major versions, complex breaking changes)
- **Breaking Changes:**
  - v18: FileWithPath type strictness; File no longer assignable
  - v19: `onDropAccepted` callback logic changed — now accepts files up to limit instead of rejecting batch
  - v20: Node.js 22+ required (drops 20 support)
- **Codebase Impact:** FileInput.tsx uses useDropzone with custom onDrop logic — requires significant Authorisations System code review
- **Blockers:** 
  - Multiple major versions with cumulative breaking changes
  - onDrop callback logic differs significantly from v15
  - Node.js version requirement (currently running 22, so this is OK, but combined with other changes makes risky)
- **Decision:** Defer until willing to do thorough FileInput.tsx refactor + testing
- **When Ready:** Plan dedicated session with thorough testing of file upload workflows
- **Estimated Effort:** 2-4 hours (release note review, code changes, testing)

**@testing-library/jest-dom 7.x** (from 6.9.1)
- **Status:** ⛔ Blocked (peer dependency changes + Node.js requirement)
- **Breaking Changes:**
  - New required peer dependency: `@testing-library/dom` must be added
  - Node.js 22+ required
  - Bug fix for vitest support (positive)
- **Codebase Impact:** Must add `@testing-library/dom` to package.json
- **Blockers:** Requires peer dependency addition, ecosystem coordination needed
- **Decision:** Defer — coordinate with other testing library upgrades
- **When Ready:** When ready to add new peer dependency and verify Node.js 22 fully compatible
- **Estimated Effort:** 30 minutes (dependency addition + testing)

**typescript 7.x** (from 6.0.3)
- **Status:** ⛔ Blocked (insufficient information, likely breaking changes)
- **Breaking Changes:** Unknown (TypeScript release notes not accessible during investigation)
- **Likely Node.js 22+ requirement**
- **Codebase Impact:** Full build system testing required, ESLint configuration may need updates
- **Blockers:** Cannot assess without seeing breaking changes
- **Decision:** Defer — wait for TypeScript 7.x to stabilise, then assess separately
- **When Ready:** When TypeScript documentation is available and project needs latest features
- **Estimated Effort:** 2-4 hours (investigation + full build testing)

**jsdom 30.x** (from 29.1.1)
- **Status:** ⛔ Blocked (part of multi-package upgrade chain)
- **Breaking Changes:** None documented (positive)
- **Likely Node.js 22+ requirement**
- **Codebase Impact:** Test environment library — no code changes, but ecosystem testing needed
- **Blockers:** Part of broader upgrade chain (react-dropzone v20, testing-library/jest-dom v7, etc.)
- **Decision:** Defer — only upgrade when doing comprehensive testing library/browser stack upgrade
- **When Ready:** As part of major testing infrastructure upgrade
- **Estimated Effort:** 1 hour (test run + verification)

**@types/node 26.x** (from 25.9.5)
- **Status:** ⛔ Blocked (type strictness changes)
- **Breaking Changes:** Major version likely introduces stricter type definitions
- **Likely Node.js 22+ requirement**
- **Codebase Impact:** May require type annotation updates in build/config files
- **Blockers:** Requires full build system testing + code review
- **Decision:** Defer — only upgrade when confident in TypeScript + build changes
- **When Ready:** Coordinate with TypeScript 7.x upgrade
- **Estimated Effort:** 1-2 hours (build testing + possible type fixes)

---

## Documentation and References

### How to Use This Document

**For routine upgrades:**
- Follow "Workflow: Backend Dependencies" or "Workflow: Frontend Dependencies"
- Use the checklist in each workflow
- Refer to "Common Pitfalls" for quick reference

**For major upgrades:**
- Check "Pending Upgrades with Breaking Changes" for known blockers
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

#### Backend Iteration 1
- Upgraded 19 backend packages
- Investigated 5 major/minor versions for breaking changes
- Identified 2 blocked packages (pyee 14.0.0, Django 6.1)
- All 265 unit/API tests passing
- E2E tests: 25 passed (infrastructure issues unrelated)
- Updated THIRD_PARTY_NOTICES.md and CHANGELOG.md
- **Key Learning:** DRF 3.18.0 breaking change in list-serializer error format required codebase analysis to confirm no impact

#### Frontend Iteration
- Executed `npm outdated` → identified 29 upgradable frontend packages
- Categorised packages: 14 safe patches, 7 high-risk (major versions), 8 moderate-risk (minor versions)
- Upgraded 19 safe packages (zero code changes): react 19.2.8, react-dom 19.2.8, react-router 7.18.2, tailwindcss 4.3.3, @tailwindcss/vite 4.3.3, vitest 4.1.10, @vitejs/plugin-react-swc 4.3.3, @vitest/coverage-istanbul 4.1.10, @types/react 19.2.18, @types/react-dom 19.2.4, @types/node 25.9.5, @testing-library/user-event 14.6.4, eslint-plugin-react-refresh 0.5.4, @iconify-json/vscode-icons 1.2.72, axios 1.19.0, eslint 10.8.1, globals 17.11.0, msw 2.15.0, typescript-eslint 8.67.0
- Blocked 6 packages: react-hook-form 7.85.0 (TypeScript type change requires code modifications), react-dropzone v20 (5 major versions with breaking changes), @testing-library/jest-dom v7 (new peer dependency), typescript v7 (major version), jsdom v30, @types/node v26
- All 292 frontend unit tests passing
- All 59 E2E tests passing in 33.76s (parallel execution)
- Updated THIRD_PARTY_NOTICES.md and CHANGELOG.md with frontend versions
- **Key Learning:** TypeScript definition changes requiring code modifications = not a safe upgrade. Principle: safe upgrades = zero code changes

