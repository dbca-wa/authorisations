# Dependency Upgrade Guidelines

This document provides a comprehensive, process-driven approach to upgrading both backend and frontend dependencies. It consolidates learnings from multiple upgrade sessions, breaking-change investigations, and test validations.

**Last Updated:** 2026-11-03 (Completed: Sessions 1-5 with 95+ total package upgrades — 21 backend (Session 3) + 15 backend (Session 4) + 11 backend (Session 5) + 29 frontend (Session 3) + 14 frontend (Session 5) across reliability, security, and dependency maintenance workflows)

**Status Summary:**
- ✅ **Deployable Now:** 344 backend tests + 363/363 frontend tests all passing
- ✅ **95+ packages upgraded:** 21 backend (Session 3) + 15 backend (Session 4) + 11 backend (Session 5) + 29 frontend (Session 3) + 14 frontend (Session 5)
- ⏸️ **3 dependencies intentionally deferred:** Django 6.1 (backend), TypeScript 7.x (frontend), vitest v5 (frontend)

---

## Quick Start

**This guide provides step-by-step workflows for upgrading backend and frontend dependencies with comprehensive testing and validation.** Read [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md) for mandatory conventions (npm only for frontend, no bun). Follow "Workflow: Backend Dependencies" or "Workflow: Frontend Dependencies" sequentially. **Use `npm update --depth=10` for frontend transitive upgrades** (not just `npm update`). **Run the Post-Implementation Audit Protocol after every upgrade session** to verify all 344 backend + 363 frontend tests pass and no packages remain outdated. Session logs must follow the mandatory format (package lists only, no test results or breaking-change commentary). AI agent prohibited from git write operations; user handles all commits.

---

## Session Log Format (MANDATORY)

**Every session log must follow this structure ONLY:**

```markdown
### Session N (YYYY-MM-DD): Brief Title

**Backend - X Package Updates**
- Direct: [pkg1 version, pkg2 version, ...]
- Transitive: [pkg1, pkg2, ...] (or list key ones if numerous)
- Group C (blocked): [pkg1 reason, pkg2 reason]

**Frontend - Y Package Updates**
- [pkg1 version, pkg2 version, ...]
- Deferred: [pkg1, pkg2]
```

**Rules:**
- ❌ Do NOT restate test results (tests passing is mandatory baseline)
- ❌ Do NOT include security vulnerability details or reasons
- ❌ Do NOT mention Docker, CI/CD, or deployment infrastructure
- ❌ Do NOT explain what each package does or breaking-change analysis
- ✅ DO list package names and new versions
- ✅ DO note which packages are blocked/deferred and their status
- ✅ DO keep totals accurate for historical tracking

---

## Post-Implementation Audit Protocol for Dependency Upgrades

**When to run**: After all upgrades complete and tests pass locally, before marking session complete.

**Purpose**: Verify upgrades are complete, lock files synced, and all tests pass with no regressions.

### Agent 1: Build & Syntax Auditor

**Responsibility**: Verify no compilation or syntax errors introduced by upgrades.

**Success Criteria:**
- ✅ Backend Python syntax valid (`py_compile`)
- ✅ Frontend linting passes (ESLint + TypeScript)
- ✅ Frontend build completes successfully

**Commands**:
```bash
# Backend syntax check
cd backend && poetry run python -m py_compile config/settings.py api/views.py applications/models.py

# Frontend linting and build
cd frontend && npm run lint && npm run build
```

**Expected Result**: All commands exit with code 0 (success). No syntax or type errors.

**FAIL if**: Any command returns non-zero exit code.

---

### Agent 2: Test Execution Auditor

**Responsibility**: Verify all tests pass. Zero tolerance for failures.

**Success Criteria:**
- ✅ All backend tests pass: `poetry run pytest` returns 344 tests passing
- ✅ **All frontend tests pass: 363/363 tests passing** (no exceptions, no timeouts, no flaky tests)

**Commands**:
```bash
# Backend tests
cd backend && poetry run pytest -q

# Frontend tests - ALL must pass
cd frontend && npm run test:unit
```

**Expected Result**: 
- Backend: 344 passing ✅
- Frontend: 363/363 passing ✅

**FAIL if**: 
- Any test fails for any reason
- Any test times out
- Test count is less than expected
- Backend count drops below 344
- Frontend count is less than 363

**If ANY test fails**: STOP. Investigate root cause. This indicates either:
1. Upgrade introduced a regression (fix codebase)
2. Test environment issue (fix infrastructure/timeout)
3. Test has a bug (fix test)

Do not proceed until ALL tests pass.

---

### Agent 3: Documentation Auditor

**Responsibility**: Verify CHANGELOG and dependency docs updated correctly.

**Success Criteria:**
- ✅ CHANGELOG.md has session entry with current date (YYYY-MM-DD)
- ✅ CHANGELOG entry is concise (no test counts, no technical details)
- ✅ docs/DEPENDENCY-UPGRADE.md Session N updated with current date
- ✅ Session log follows format (packages + blocked only, no extras)
- ✅ THIRD_PARTY_NOTICES.md backend section updated with new versions
- ✅ No past releases modified in CHANGELOG

**Commands**:
```bash
# Check CHANGELOG session entry
head -20 CHANGELOG.md

# Check DEPENDENCY-UPGRADE.md session log
grep -A20 "^### Session N" docs/DEPENDENCY-UPGRADE.md

# Verify versions in THIRD_PARTY_NOTICES.md
grep "^| psycopg\|^| dbca-utils" THIRD_PARTY_NOTICES.md

# Verify no past releases modified
git log --oneline CHANGELOG.md | head -5
```

**Expected Result**: Session entry dated today, concise format, versions match lock files, git history shows only additions.

**FAIL if**: Past releases modified or versions don't match lock files.

---

### Agent 4: Dependency Lock Auditor

**Responsibility**: Verify lock files properly synced with upgraded versions and NO packages remain outdated.

**Success Criteria:**
- ✅ backend/poetry.lock contains updated direct dependency versions
- ✅ frontend/package-lock.json contains updated direct dependency versions
- ✅ `npm outdated` shows ONLY intentionally deferred packages (TypeScript 7.x, vitest 5.x, etc.) — **CRITICAL** 
  - Must NOT show any other packages as outdated
  - If other packages appear, transitive update incomplete
- ✅ Lock files auto-generated (not manually edited)
- ✅ Lock files in sync with constraint files (pyproject.toml, package.json)

**Commands**:
```bash
# CRITICAL: Verify all transitive deps updated (except intentionally deferred)
cd frontend && npm outdated
# Expected: ONLY shows TypeScript 7.x, vitest 5.x, other deferred packages (no other packages listed)

# Check backend lock file for specific package
cd backend && grep -A2 "^name = \"psycopg\"" poetry.lock | head -3

# Check frontend lock file versions
cd frontend && npm ls axios eslint | head -5

# Verify lock files auto-generated
head -3 backend/poetry.lock
head -3 frontend/package-lock.json
```

**Expected Result**: 
- Versions in lock files match pyproject.toml/package.json constraints
- Files show auto-generation headers (no manual edits)
- `npm outdated` shows ONLY deferred packages (TypeScript, vitest) — indicates all non-deferred transitive deps at latest

**FAIL if**:
- Versions don't match or lock files appear manually edited
- `npm outdated` shows packages NOT in "Intentionally Deferred Dependencies" section (e.g., "follow-redirects 1.16.1 → 1.16.2") — means transitive update incomplete
  - Recovery: Run `npm update --depth=10` again, then verify with `npm outdated`, then re-run this agent

---

### Audit Execution Workflow

**Run agents in order (sequentially, not parallel):**

1. **Agent 1 (Build & Syntax)** → Must PASS before proceeding
   - If FAIL: Fix syntax errors, re-run Agent 1
2. **Agent 2 (Tests)** → Must PASS before proceeding
   - ALL 363 frontend + 344 backend tests must pass with zero exceptions
   - If FAIL: Investigate and fix, do not proceed
3. **Agent 3 (Documentation)** → Must PASS before proceeding
   - If FAIL: Update docs, re-run Agent 3
4. **Agent 4 (Lock Files)** → Must PASS before proceeding
   - If FAIL: Regenerate lock files, re-run Agent 4

**If all agents PASS**: Session complete and ready for deployment.

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

### Phase 7: Upgrade Transitive Dependencies

After direct dependencies are upgraded and tested, upgrade transitive dependencies (dependencies of your dependencies) to latest patch versions:

```bash
cd backend
poetry update
```

This command:
- Upgrades all transitive dependencies to latest patch/minor versions
- Respects all version ranges (upper/lower bounds) in `pyproject.toml`
- Regenerates `poetry.lock` automatically
- Does NOT modify `pyproject.toml` or `poetry.toml`

**Verify compatibility:**
```bash
cd backend && poetry run pytest
```

All tests must pass. If transitive upgrades introduce regressions:

```bash
# Revert and identify the problematic package
git checkout poetry.lock

# Run audit to see what's needed
poetry show --outdated

# Consider deferring problematic transitive deps to next cycle
# Document in DEPENDENCY-UPGRADE.md "Intentionally Deferred Dependencies"
```

### Phase 8: Update Documentation

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
- Backend dependency upgrades: Updated 19 packages including Django 5.2.17 (security patches), cryptography 50.0.0, cffi 2.1.1, djangorestframework 3.18.0, pytest-django 4.14.0, and other packages. See THIRD_PARTY_NOTICES.md for complete version list.
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

### Phase 8: Upgrade Transitive Dependencies

After direct dependencies are upgraded and tested, upgrade transitive dependencies to latest patch versions:

```bash
cd frontend

# IMPORTANT: npm update alone does NOT update nested transitive dependencies
# (e.g., axios → follow-redirects → [outdated version])
# Use --depth=10 to recursively update all transitive chain dependencies
npm update --depth=10
```

This command:
- Upgrades all transitive dependencies (direct + all nested chains) to latest patch/minor versions
- Respects all version ranges (^, ~) in `package.json`
- Regenerates `package-lock.json` automatically with all transitive updates
- Does NOT modify `package.json`
- **Critical:** --depth=10 ensures nested transitive packages (e.g., follow-redirects via axios) are caught

**Verify no packages remain outdated:**
```bash
cd frontend

# Run full verification suite
npm update --depth=10
npm outdated          # Should show ONLY deferred packages (TypeScript 7.x, vitest 5.x) — not empty, not unintended outdated packages
npm run lint && npm run build && npm run test:unit
```

All tests and linting must pass. **If `npm outdated` shows packages NOT in the "Intentionally Deferred Dependencies" list, the transitive update is incomplete — re-run `npm update --depth=10`.**

If transitive upgrades introduce regressions:

```bash
# Revert and identify the problematic package
git checkout package-lock.json

# Check for vulnerabilities or outdated transitive deps
npm audit
npm ls

# Consider deferring problematic transitive deps to next cycle
# Document in DEPENDENCY-UPGRADE.md "Intentionally Deferred Dependencies"
```

### Phase 9: Run E2E Tests

After frontend upgrades, always validate end-to-end:

```bash
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope
```

**With diagnostics (if tests fail):**
```bash
cd backend && poetry run pytest e2e/tests -v -n auto --dist loadscope --tracing=retain-on-failure --screenshot=only-on-failure
```

**Note:** E2E tests run in parallel (`-n auto`) for faster execution (recent baseline: 63 tests in under 2 minutes, environment dependent).

### Phase 10: Update Documentation

Same as backend: update [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) frontend section and [CHANGELOG.md](../CHANGELOG.md).

---

## Critical Risks

**Lock File Sync:** Always run `poetry lock` (backend) or `npm install` (frontend) after updating constraint files. CI will fail with "lock file out of sync" if skipped.

**Transitive Updates:** `npm update` alone does NOT update nested transitive dependencies. Use `npm update --depth=10` to catch packages like follow-redirects via axios. Run `npm outdated` after to verify ONLY deferred packages show as outdated; if other packages appear, run `npm update --depth=10` again.

**Verify Actual Usage:** When breaking changes are documented, search the Authorisations System codebase to confirm the affected API is actually used. Many breaking changes don't apply to this application's usage patterns.

---

## Intentionally Deferred Dependencies

**3 major dependencies** are intentionally deferred. These require either dedicated sessions or ecosystem readiness:

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

**vitest v5.x** (from 4.1.12)
- **Status:** ⏸️ Intentionally deferred (ecosystem compatibility issue)
- **Reason:** vitest 5.x has type declaration conflict with @testing-library/jest-dom 7.0.1 — both declare `interface Assertion` with incompatible type parameters (vitest 5: `<Return, Received>`, jest-dom 7: `<T = any>`). This is a known ecosystem incompatibility from two newly released packages.
- **Technical Details:** TypeScript error TS2428 "All declarations of 'Assertion' must have identical type parameters" prevents `npm run lint` and `npm run build` from succeeding (test execution unaffected, type checking affected)
- **Investigation Completed:** 
  - ✅ Confirmed vitest 5.x supports Node 22+ ✅ No code changes needed for tests
  - ✅ Confirmed @testing-library/jest-dom 7.0.1 is compatible with vitest 4.1.12 ✅ No type conflict with v4
  - ✅ Confirmed msw 3.0.0 works perfectly with vitest 4.1.12
  - ✅ Applied security patch: vitest 4.1.10 → 4.1.11 (GHSA-82fw-gwwq-j7x9 Path Traversal / Arbitrary File Read)
  - ✅ Current: vitest 4.1.12, @testing-library/jest-dom 7.0.1, all 363 tests passing
- **When to Upgrade:** After ecosystem publishes:
  - Option A: vitest 5.0.3+ with fixed Assertion interface matching jest-dom 7.x declarations, OR
  - Option B: jest-dom 7.0.2+ with Assertion interface matching vitest 5.0.x declarations, OR
  - Option C: TypeScript issue resolved (both projects align type signatures)
- **Estimated Effort:** 30 minutes once ecosystem stabilises (just update package.json + npm install + revalidate tests)
- **Current State:** vitest 4.1.12, @testing-library/jest-dom 7.0.1, all 363 tests passing, full build successful

---

## Session History

### Session 1 (2026-08-13): Initial Investigation
- Identified upgrade candidates and planned two-phase approach (backend first, then frontend)

### Session 2 (2026-08-13): Initial Dependency Upgrades

**Backend - 19 Package Updates**
- psycopg, django-vite, gunicorn, djangorestframework, playwright, and 14 others
- Group C (blocked): pyee 14.0.0, Django 6.1

**Frontend - 19 Package Updates**
- react 19.2.8, react-dom 19.2.8, react-router 7.18.2, tailwindcss 4.3.3, @tailwindcss/vite 4.3.3, vitest 4.1.11, @vitejs/plugin-react-swc 4.3.3, @vitest/coverage-istanbul 4.1.11, @types/react 19.2.18, @types/react-dom 19.2.4, @types/node 25.9.5, @testing-library/user-event 14.6.4, eslint-plugin-react-refresh 0.5.4, @iconify-json/vscode-icons 1.2.72, axios 1.19.0, eslint 10.8.1, globals 17.11.0, msw 2.15.0, typescript-eslint 8.67.0
- Blocked: react-hook-form 7.85.0, react-dropzone v20, @testing-library/jest-dom v7, typescript v7, jsdom v30, @types/node v26

### Session 3 (2026-09-25 → 2026-09-30): Testing Infrastructure & Major Frontend Migrations

**Backend - 21 Package Updates**
- psycopg, django-vite, gunicorn, djangorestframework, playwright, and 16 others
- Group C (blocked): Django 6.1, pyee 14.0.0

**Frontend - 29 Package Updates**
- Direct: @testing-library/dom 10.4.0, @testing-library/jest-dom 7.0.1, jsdom 30.1.1, react-hook-form 7.89.0, msw 3.0.0, react-router 8.4.0, react-dropzone 20.1.2, vitest 4.1.11, and 21 others
- Deferred: typescript 7.0.2, vitest 5.x

### Session 4 (2026-10-21): Dependency Refresh

**Backend - 15 Package Updates**
- Direct: certifi 2026.10.19, playwright 1.64.0, pytest-playwright 0.10.0, pyee 14.0.0, pycparser 3.11, and 10 others
- Group C (blocked): Django 6.1.2

**Frontend - 22 Direct + 32 Transitive Updates**
- react, @mui, vite, vitest, eslint, typescript-eslint, and others
- Deferred: typescript 7.x, vitest 5.x

### Session 5 (2026-11-03): Backend & Frontend Patch/Minor Updates

**Backend - 11 Package Updates**
- Direct: playwright 1.64.1, psycopg 3.3.7, dbca-utils 3.0.16
- Transitive: certifi 2026.10.23, pycparser 3.12, asgiref 3.13.0, wcwidth 0.9.4, azure-storage-blob 12.31.1, coverage 7.17.0, pytest 9.2.0, frozendict 2.5.0, sqlparse, psycopg-binary, ipython, and supporting libraries
- Group C (blocked): Django 6.1.2, pyee 16.0.0

**Frontend - 14 Direct Package Updates**
- @mui/x-data-grid 9.17.0, @mui/x-date-pickers 9.17.0, axios 1.21.0, eslint 10.14.0, @vitejs/plugin-react 6.2.1, globals 17.14.0, react-hook-form 7.91.0, react-router 8.5.1, @tailwindcss/vite 4.3.4, tailwindcss 4.3.4, vite 8.3.5, typescript-eslint 8.72.1, @types/node 26.6.6, @iconify-json/vscode-icons 1.2.95
- Deferred: typescript 7.0.2, vitest 5.1.0
