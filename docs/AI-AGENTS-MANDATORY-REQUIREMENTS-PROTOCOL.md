# AI Agents: Mandatory Requirements & Multi-Agent Audit Protocol

**Purpose**: Define non-negotiable requirements for all AI-driven development and specify how to audit implementation with multiple focused agents.

**Scope**: All feature development, bugfixes, and code review sessions involving AI agents.

---

## Part 1: Pre-Work Protocol (Every Session Start)

Before responding to any user request, **in order**:

### Step 1: Read Full Documentation (Not Skim)
Read completely:
- `FEATURE-DEVELOPMENT.md` (all sections, end-to-end)
- `ARCHITECTURE.md`
- `BACKEND-CONVENTIONS.md`
- `FRONTEND-CONVENTIONS.md`
- Any docs referenced in the current task

### Step 2: Extract Mandatory Requirements
From FEATURE-DEVELOPMENT.md, identify which apply to this task:
- Package managers: npm-only frontend, poetry backend
- Code structure: file locations, layers, organization
- Security: ownership scoping, read vs write checks
- Imports: module-level only, PEP 8, no function-level imports except unavoidable circular imports (documented)
- Test coverage: when required, where to place tests, layers
- Test file naming: `test_*.py` convention with specific prefixes
- Security marker: `@pytest.mark.security` for access control tests
- Documentation: JSDoc/docstrings for every function, comments for non-obvious logic
- Code quality: syntax/types BEFORE tests (blocking rule)
- CHANGELOG: impact-focused, one entry per feature, never modify past releases
- Pre-submission checklist: all items required unless explicit override

### Step 3: Ask Clarifying Questions
If the request is ambiguous:
- What problem does this solve (user-facing outcome)?
- Which layers are affected (frontend, backend, both)?
- Are there security implications (ownership, permissions)?
- What test coverage is required?

### Step 4: Plan Mandatory Requirements Application
List exactly which mandatory requirements apply. Example:
- ✅ Backend code structure (models, serializers, views)
- ✅ Security checks (owner-only write, has_access for read)
- ✅ Imports at module level
- ✅ Test coverage (API + security)
- ✅ JSDoc comments on all functions
- ✅ CHANGELOG entry
- ❌ Frontend changes (not applicable to this task)
- ❌ E2E tests (not mission-critical)

### Step 5: State Compliance Commitment
Explicitly confirm before coding:
"I will apply the following mandatory requirements:
- Import all dependencies at module level (zero exceptions without comment)
- Run syntax/type checks before any tests
- Write tests in correct locations with proper naming
- Add JSDoc/docstrings to all functions
- Update CHANGELOG with impact-focused entry
- Update relevant documentation"

---

## Part 2: Mandatory Requirements (Extracted from FEATURE-DEVELOPMENT.md)

### 2.1 Code Structure & Organization

#### Backend
- **Models**: app `models.py`
- **Serializers**: app `serialisers.py` (use British spelling)
- **Views/API**: `backend/api/views.py` for viewsets, `backend/{app}/views.py` for non-API views
- **Management commands**: `backend/{app}/management/commands/{command_name}.py`
- **N+1 prevention**: Use `select_related()` on known FK paths for list/retrieve endpoints
- **Naming**: Use British English: `normalise`, `authorisation`

#### Frontend
- **Component definitions**: Use `const` for components, not `function` declarations
- **Imports**: Explicit named exports/imports (safer refactoring than defaults)
- **Import grouping**: Default imports first, then named/type imports (with braces), blank line between
- **Naming**: British English: `normalise`, `authorisation`

### 2.2 Imports: MANDATORY MODULE-LEVEL ONLY

**Rule**: ALL imports at module level (top of file), following PEP 8.

**No exceptions except**: Unavoidable circular imports (documented with comment explaining the circular dependency).

**Example of violation** (import inside function):
```python
def test_load_targets_missing_setting_raises_error(self, monkeypatch):
    from django.conf import settings  # ❌ VIOLATION
```

**Correct approach** (module level):
```python
from django.conf import settings

class TestLoadTargets:
    def test_load_targets_missing_setting_raises_error(self, monkeypatch):
        monkeypatch.delattr(settings, "SCHEMA_MIGRATION_TARGETS", raising=False)
```

**When circular imports are unavoidable** (rare):
```python
# Module A
from module_b import something  # Circular: Module B imports Module A

# Rare exception: Import inside function to break cycle
def my_function():
    # Import here to avoid circular dependency at module load time
    # (This is unavoidable due to: Module B needs X from Module A,
    #  and Module A needs Y from Module B)
    from module_b import something_else
```

**Verification command**:
```bash
grep -n "^[[:space:]]\+\(import\|from\)" file.py
# Output: any line with leading whitespace before import = VIOLATION
```

### 2.3 Code Quality: Syntax & Types BEFORE Tests

**Blocking rule**: Do NOT run tests until syntax and type errors are fixed.

**Backend**:
```bash
cd backend
# Step 1: Check Python syntax
poetry run python -m py_compile path/to/file.py

# Step 2: Type check (if mypy enabled)
poetry run python -m mypy --config-file=pyproject.toml path/to/file.py

# Step 3: ONLY THEN run tests
poetry run pytest
```

**Frontend**:
```bash
cd frontend
# Step 1: Lint and type check
npm run lint

# Step 2: Build check (catches type errors)
npm run build

# Step 3: ONLY THEN run tests
npm run test:unit
```

### 2.4 Security: Mandatory Patterns

**Read paths** (accessing application data for viewing):
- Use `Application.has_access(user)` → grants access to owner OR reviewer-group members
- Soft 404 pattern: If access denied, return 404 (not 403) to avoid exposing internal roles

**Write paths** (modifying application data):
- Use explicit `application.owner == request.user` check
- No reviewers allowed for writes
- Always check `request.user.is_authenticated` before accessing user attributes (avoid AttributeError on AnonymousUser)

**Attachment access**:
- Enforce ownership checks on attachment querysets (soft-delete pattern)
- Document the access pattern: is this read (has_access) or write (owner-only)?

### 2.5 Documentation: Mandatory for Every Function

**Backend (Python docstrings)**:
```python
def apply_schema_migration(self, document: dict, version_path: str) -> dict:
    """Apply schema migration to document.
    
    Transforms document structure from previous_schema to target_schema.
    Modifies version_path in-place.
    
    Args:
        document: JSON document to migrate
        version_path: dot-notation path to schema version field
        
    Returns:
        Modified document with schema_version incremented
        
    Raises:
        ValueError: If document doesn't match previous_schema
    """
    # Implementation
```

**Frontend (JSDoc)**:
```typescript
/**
 * Transforms application list by applying sort order.
 * 
 * Handles sorting by status, date, applicant name. Returns stable sorted copy
 * without modifying original array. Supports reverse sort (descending order).
 * 
 * @param apps - Array of applications to sort
 * @param order - Sort order (e.g., "updated-desc", "name-asc")
 * @returns New sorted array
 */
const applySortOrder = (apps: Application[], order: string): Application[] => {
  // Implementation
};
```

**Single-line comments for non-obvious logic**:
```python
# Only show the sort option if user has submitted at least one application
if has_submitted_applications(user_apps):
    sort_options.append("most_recent")
```

### 2.6 Test Coverage & Placement

**When tests are required**:
- ✅ New data model or logic: backend unit tests
- ✅ New API endpoint: backend API tests + security tests
- ✅ Read/write access change: security tests (mandatory)
- ✅ New React component: frontend unit tests
- ✅ New dialog/form/workflow: all layers (backend unit, API, security, frontend unit, E2E if mission-critical)
- ✅ Bugfix with ownership implication: security tests
- ❌ UI cosmetic change: no tests required
- ❌ Documentation-only change: no tests required

**Test file naming convention** (backend):
- `test_models.py` — Unit tests for models and model logic
- `test_serialisers.py` — Serializer validation tests
- `test_views_security.py` — Non-API view access control (marked with `@pytest.mark.security`)
- `test_api_endpoint_security.py` — API endpoint authorization (marked with `@pytest.mark.security`)
- `test_forms.py` — Form field and validation tests
- `test_management_commands.py` — Management command tests

**Security tests organization**:
- Co-located with application tests in `app/tests/` (not separate folder)
- Use `@pytest.mark.security` marker for logical grouping
- File naming makes purpose clear: `*_security.py`
- Test both positive (access granted) and negative (denied, 403/404) cases

**Test structure**:
- Use `pytest.fixture` for realistic test data
- Use `@pytest.mark.security` for access control tests
- Verify both "should be allowed" and "should be denied" paths
- Test latest-version selection for questionnaires
- Test N+1 prevention (verify select_related used)

### 2.7 CHANGELOG: Mandatory Format

**Rule**: One entry per feature/fix, impact-focused, concise, never modify past releases.

**Format**:
```markdown
## [X.Y.Z] - Unreleased

### Added
- Added sorting options to application list for better workflow management.

### Fixed
- Fixed attachment visibility for reviewers in queue view.

### Changed
- Renamed sort option "most recent" to "updated newest" for consistency.
```

**What NOT to do**:
- ❌ Modify past release notes (corrupts audit trail)
- ❌ Technical implementation details ("Refactored applicationUtils.tsx to...")
- ❌ Multiple entries for one feature
- ❌ Vague entries ("Updated things")

**Version management**:
- Check `VERSION` file and `CHANGELOG.md`
- If latest version in CHANGELOG has past date → it's released → create new `[X.Y.Z] - Unreleased` section
- If `Unreleased` section exists → add entry to it
- Never backdate entries or modify historical releases

### 2.8 Pre-Submission Checklist (Mandatory)

Before marking work complete:
- [ ] **Syntax/types pass**: `poetry run python -m py_compile` (backend) or `npm run lint` (frontend)
- [ ] **Tests written**: Correct location, correct file naming, correct markers
- [ ] **Tests passing**: `cd backend && poetry run pytest` (all tests, not just new ones)
- [ ] **Imports at module level**: Zero indented imports (except documented circular imports)
- [ ] **Security verified**: Ownership scoping applied, read vs write rules checked
- [ ] **JSDoc/docstrings**: Every function documented
- [ ] **CHANGELOG updated**: Impact-focused, one entry per feature
- [ ] **Project docs updated**: Architecture, conventions, API flows, or testing docs as needed
- [ ] **No breaking changes**: Existing tests still pass
- [ ] **API contracts aligned**: Frontend types match backend payloads (if applicable)

---

## Part 3: Multi-Agent Post-Implementation Audit Protocol

**Purpose**: Prevent failures like the import violation by using multiple focused agents, each with one clear responsibility.

**Why**: A single overloaded audit dilutes attention and misses details. Specialized agents catch what general audits miss.

### 3.1 Agent Roles & Responsibilities

#### Agent 1: Structural Compliance Auditor
**Responsibility**: Verify file locations, package structure, deleted files, protected files.

**Success criteria**:
- ✅ All 9 deleted files confirmed deleted (find command returns empty)
- ✅ All protected files unchanged (git diff returns empty for protected files)
- ✅ All code in correct locations (models in models.py, serializers in serialisers.py, views in views.py, management commands in management/commands/, tests in tests/)
- ✅ No files moved or reorganized outside scope

**Commands to run**:
```bash
# Verify deleted files
find backend/questionnaires -name "schema_migrations_loader.py" -o -name "schema_migration_utils.py"
# Expected: (empty output = success)

# Verify protected files unchanged
git diff HEAD -- backend/questionnaires/models.py backend/questionnaires/serialisers.py
# Expected: (empty output = success)

# Verify file locations
find backend -name "views.py" | grep questionnaires
find backend -name "serialisers.py" | grep questionnaires
find backend -name "models.py" | grep questionnaires
# Expected: files in correct locations
```

**Output format**:
```
## Structural Compliance Audit: PASS/FAIL

### Deleted Files
- schema_migrations_loader.py: ✅ Deleted
- schema_migration_utils.py: ✅ Deleted
...

### Protected Files
- models.py: ✅ Unchanged (git diff empty)
- serialisers.py: ✅ Unchanged (git diff empty)
...

### File Organization
- Views: ✅ In backend/api/views.py or app/views.py
- Serializers: ✅ In app/serialisers.py
- Models: ✅ In app/models.py
...

### Result: PASS/FAIL with specific violations if any
```

---

#### Agent 2: Import Compliance Auditor
**Responsibility**: Verify ALL imports are at module level, zero indented imports (except documented circular).

**Success criteria**:
- ✅ Zero indented `import` statements in any modified Python file (except documented circular imports)
- ✅ All imports at top of file (lines 1-30 typically)
- ✅ Import groups organized: stdlib, third-party, local

**Commands to run**:
```bash
# Find ALL indented imports (= violations)
grep -rn "^[[:space:]]\+\(import\|from\)" backend/ --include="*.py"
# Expected: (empty output = success)

# Read file to verify import organization
read_file backend/schema_migration_framework/tests/test_registry.py lines 1-60
# Expected: all imports in lines 1-20, no imports inside function definitions
```

**Violation detection**:
```bash
# For each file, check:
grep -n "def test_.*:" file.py  # Find test methods
grep -n "^[[:space:]]*from\|^[[:space:]]*import" file.py  # Find indented imports
# If indented import comes AFTER a function def line → VIOLATION
```

**Output format**:
```
## Import Compliance Audit: PASS/FAIL

### Modified Files Checked
- test_registry.py: ✅ No indented imports (15 module-level imports verified)
- settings.py: ✅ No indented imports (8 module-level imports organized)
- executor.py: ✅ No indented imports (except line 42: documented circular import)
...

### Violations Found
None / OR
- test_registry.py, line 49: `from django.conf import settings` inside method (VIOLATION)
- executor.py, line 42: `import module_b` inside function (VIOLATION)
...

### Result: PASS/FAIL
```

---

#### Agent 3: Syntax & Type Auditor
**Responsibility**: Verify no syntax errors, type checking passes, linting passes.

**Success criteria**:
- ✅ Python files compile without syntax errors (`py_compile` returns zero errors)
- ✅ TypeScript/linting passes (`npm run lint` returns zero errors)
- ✅ Build succeeds (frontend `npm run build` succeeds)
- ✅ Type checking passes (mypy, TypeScript strict mode)

**Commands to run**:
```bash
# Backend: syntax check
cd backend && poetry run python -m py_compile backend/schema_migration_framework/tests/test_registry.py

# Frontend: linting
cd frontend && npm run lint

# Frontend: type check and build
cd frontend && npm run build

# Backend: type check (if mypy enabled)
cd backend && poetry run python -m mypy --config-file=pyproject.toml backend/
```

**Output format**:
```
## Syntax & Type Auditor: PASS/FAIL

### Python Files
- py_compile backend/schema_migration_framework/tests/test_registry.py: ✅ OK
- py_compile backend/schema_migration_framework/executor.py: ✅ OK
...

### Type Checking
- mypy backend/: ✅ 0 errors
...

### Frontend Linting & Build
- npm run lint: ✅ 0 errors
- npm run build: ✅ Success
...

### Result: PASS/FAIL
```

---

#### Agent 4: Test Coverage & Execution Auditor
**Responsibility**: Verify tests exist in correct locations, use correct naming, run and pass.

**Success criteria**:
- ✅ Test files in correct locations (`app/tests/test_*.py` pattern)
- ✅ Security tests use `@pytest.mark.security` marker
- ✅ Test file naming follows convention (`test_models.py`, `test_api_endpoint_security.py`, etc.)
- ✅ All new tests pass: `poetry run pytest` returns zero failures
- ✅ Existing tests still pass (no regressions)

**Commands to run**:
```bash
# Find test files
find backend -name "test_*.py" -type f | sort

# Run all backend tests
cd backend && poetry run pytest -v

# Run with coverage
cd backend && poetry run pytest --cov

# Run frontend tests
cd frontend && npm run test:unit
```

**Output format**:
```
## Test Coverage & Execution Auditor: PASS/FAIL

### Test File Organization
- questionnaires/tests/test_models.py: ✅ Found, 18 tests
- questionnaires/tests/test_schema_migration_0001.py: ✅ Found, 12 tests
- schema_migration_framework/tests/test_registry.py: ✅ Found, 28 tests
...

### Security Markers
- test_api_endpoint_security.py: ✅ Uses @pytest.mark.security
- test_views_security.py: ✅ Uses @pytest.mark.security
...

### Test Execution
- Total tests run: 142
- Passed: 142 ✅
- Failed: 0 ✅
- Skipped: 0
...

### Result: PASS/FAIL
```

---

#### Agent 5: Security Auditor
**Responsibility**: Verify ownership scoping, permission checks, read vs write patterns.

**Success criteria**:
- ✅ All API endpoints touching application data use correct access pattern:
  - Read: `Application.has_access(user)` or soft 404
  - Write: `application.owner == request.user`
- ✅ Security tests verify both positive (allowed) and negative (denied, 404) cases
- ✅ All QuerySets have ownership filtering applied
- ✅ All views check `request.user.is_authenticated` before accessing user attributes
- ✅ Attachment access enforced (soft-delete with ownership check)

**Commands to run**:
```bash
# Search for application access patterns
grep -rn "has_access\|owner == request.user" backend/ --include="*.py"

# Search for QuerySet filtering
grep -rn "filter(owner=\|filter(application__owner=" backend/ --include="*.py"

# Search for permission checks
grep -rn "is_authenticated" backend/ --include="*.py"

# Run security-marked tests
cd backend && poetry run pytest -m security -v
```

**Output format**:
```
## Security Auditor: PASS/FAIL

### Read Endpoints
- GET /api/applications/: ✅ Uses has_access()
- GET /api/applications/{id}/: ✅ Uses has_access() with soft 404
...

### Write Endpoints
- PATCH /api/applications/{id}/: ✅ Checks owner == request.user
- DELETE /api/applications/{id}/: ✅ Checks owner == request.user
...

### QuerySet Filtering
- Questionnaire.objects.filter(): ✅ Filters by owner
- Attachment.objects.filter(): ✅ Filters by owner
...

### Authentication Checks
- All views check request.user.is_authenticated: ✅
...

### Security Tests
- Security tests passed: 28 ✅
- Both positive and negative cases covered: ✅
...

### Result: PASS/FAIL
```

---

#### Agent 6: Documentation Auditor
**Responsibility**: Verify JSDoc/docstrings exist, CHANGELOG updated, project docs current.

**Success criteria**:
- ✅ Every function has JSDoc (frontend) or docstring (backend)
- ✅ CHANGELOG has one impact-focused entry per feature
- ✅ CHANGELOG never modified past releases
- ✅ Relevant project docs updated (ARCHITECTURE, conventions, API flows)
- ✅ Non-obvious logic has single-line comments explaining WHY

**Commands to run**:
```bash
# Search for functions without docstrings (Python)
grep -n "^def " backend/file.py | while read line; do
  line_num=$(echo $line | cut -d: -f1)
  if ! grep -A1 "^def " backend/file.py | grep -q '"""'; then
    echo "Missing docstring at line $line_num"
  fi
done

# Search for functions without JSDoc (TypeScript)
grep -n "const.*=" frontend/src/file.tsx | grep -v "^[[:space:]]*/\\*\\*"

# Check CHANGELOG
head -30 CHANGELOG.md  # Verify format and content

# Check if past releases modified
git log --oneline CHANGELOG.md | head -20  # Verify no recent edits to released versions
```

**Output format**:
```
## Documentation Auditor: PASS/FAIL

### Backend Docstrings
- executor.py functions: ✅ All have docstrings (12/12)
- registry.py functions: ✅ All have docstrings (8/8)
...

### Frontend JSDoc
- components: ✅ All have JSDoc (15/15)
- context: ✅ All have JSDoc (6/6)
...

### CHANGELOG
- Latest entry: ✅ "Added sorting options to application list"
- Format: ✅ Impact-focused, concise
- Past releases modified: ✅ No (git log shows only version section additions)
...

### Project Documentation Updated
- ARCHITECTURE.md: ✅ Updated with new data model
- BACKEND-CONVENTIONS.md: ✅ Updated with new patterns
- FRONTEND-CONVENTIONS.md: ✅ (No changes needed)
...

### Result: PASS/FAIL
```

---

#### Agent 7: API Contract Auditor (if frontend changes)
**Responsibility**: Verify frontend types match backend payloads, serializers aligned.

**Success criteria**:
- ✅ TypeScript interfaces match Django serializer fields
- ✅ Optional fields in backend (`allow_null=True`) are optional in frontend (`?: type`)
- ✅ Required fields in backend are non-optional in frontend
- ✅ API manager calls updated to match new endpoints
- ✅ No type mismatches between frontend and backend

**Commands to run**:
```bash
# Extract backend serializer fields
grep -A50 "class.*Serializer" backend/api/serialisers.py

# Check frontend type definitions
grep -A20 "interface.*{" frontend/src/types.ts

# Verify API manager calls
grep -n "apiClient\|fetch\|axios" frontend/src/context/ApiManager.ts
```

**Output format**:
```
## API Contract Auditor: PASS/FAIL

### Backend Serializers
- ApplicationSerializer:
  - id: integer ✅
  - title: string ✅
  - status: enum ✅
...

### Frontend Type Definitions
- Application interface:
  - id: number ✅
  - title: string ✅
  - status: "draft" | "submitted" | ... ✅
...

### API Manager Updates
- GET /applications: ✅ Updated
- PATCH /applications/{id}: ✅ Updated
...

### Type Alignment
- All serializer fields have matching TypeScript types: ✅
- Optional fields match allow_null: ✅
...

### Result: PASS/FAIL
```

---

### 3.2 Audit Execution Workflow

**When to run audit**: After implementation complete, before marking "ready for review".

**Audit sequence** (in order, not parallel):

1. **Agent 1 (Structural)** → Must PASS before proceeding
   - If FAIL: Stop, fix file locations, re-run Agent 1
2. **Agent 2 (Imports)** → Must PASS before proceeding
   - If FAIL: Stop, move imports to module level, re-run Agent 2
3. **Agent 3 (Syntax/Types)** → Must PASS before proceeding
   - If FAIL: Stop, fix syntax errors, re-run Agent 3
4. **Agent 4 (Tests)** → Must PASS before proceeding
   - If FAIL: Stop, fix failing tests, re-run Agent 4
5. **Agent 5 (Security)** → Must PASS before proceeding
   - If FAIL: Stop, fix permission checks, re-run Agent 5
6. **Agent 6 (Documentation)** → Must PASS before proceeding
   - If FAIL: Stop, add docstrings/CHANGELOG, re-run Agent 6
7. **Agent 7 (API Contract, if applicable)** → Must PASS before proceeding
   - If FAIL: Stop, align types, re-run Agent 7

**If all agents PASS**: Implementation ready for review.

**If any agent FAILS**: Fix violation, re-run only that agent (not full audit).

---

### 3.3 Audit Instructions Template

**Use this template for each agent call**:

```
## AGENT {N}: {AGENT_NAME}

### Responsibility
{Clear one-sentence responsibility}

### Success Criteria
{List of exact criteria, marked with ✅ if must pass}

### Commands to Run
{Exact commands, copy-pasteable, with expected output}

### Report Format
{Expected structure of report}

### Blocking Rules
- STOP immediately if any criterion fails
- Do NOT skip steps
- Do NOT modify code (only report)
- Report specific violation locations (file, line number)

### Definition of Failure
Report FAIL if:
- Any command returns non-zero exit code
- Any criterion not met
- Any violation of mandatory requirements
```

---

## Part 4: Emergency Fix Protocol (When Audit Fails)

If any agent finds violations:

### Step 1: Understand the Violation
- Read the agent's report carefully
- Note exact file, line number, and violation type
- Understand why it violates mandatory requirements

### Step 2: Fix (Do NOT implement around it)
- Make minimal fix to pass that agent's criteria
- Do NOT change other code
- Do NOT add workarounds

### Step 3: Re-Audit (Only that agent)
- Run only the failed agent's audit again
- Confirm it now PASSES

### Step 4: Continue
- If PASS: proceed to next agent
- If FAIL: repeat steps 1-3

---

## Part 5: Session Template for Every Chat

**Name this first message: "FIRST MESSAGE"**

Use this template for every new session:

---

### FIRST MESSAGE

**Before I provide any response, I will:**

1. ✅ **Read (not skim) entire FEATURE-DEVELOPMENT.md**
2. ✅ **Read all referenced documents** (ARCHITECTURE, conventions, API flows, etc.)
3. ✅ **Extract mandatory requirements** that apply to this task
4. ✅ **Ask clarifying questions** if needed
5. ✅ **Plan mandatory requirements application** (list which apply, why)
6. ✅ **State compliance commitment** before starting any work

**Mandatory requirements I will follow:**
- [ ] Code structure (correct file locations, layers)
- [ ] Imports at module level ONLY (zero exceptions without comment)
- [ ] Security rules (ownership scoping, read vs write)
- [ ] Syntax/types BEFORE tests (blocking rule)
- [ ] Test coverage (correct location, naming, markers)
- [ ] JSDoc/docstrings for every function
- [ ] CHANGELOG entry (impact-focused, one per feature)
- [ ] Documentation updates (ARCHITECTURE, conventions, etc.)
- [ ] Pre-submission checklist (all items required)

**Audit protocol:**
- After implementation, will run 7-agent post-implementation audit
- Each agent has one focused responsibility
- Audit runs in sequence (Agent 1 → 2 → 3 → ... → 7)
- Will STOP and FIX immediately if any agent reports FAIL
- Will re-run only that agent (not full audit) after fix

**I understand**: This protocol exists because I failed before. I will execute it precisely.

---

## Part 6: Why This Protocol Exists

This protocol was created because a previous implementation passed tests but violated MANDATORY REQUIREMENTS:
- Import statement inside a test method (violates module-level import rule)
- Single overloaded audit missed critical failures (40+ items in one run)
- Vague audit instructions allowed interpreter ambiguity
- No structured multi-agent approach to catch specialized violations

The 7-agent audit structure prevents this by:
- Each agent specialized in one concern (structure, imports, syntax, tests, security, docs, contracts)
- Explicit success criteria (not vague checklists)
- Concrete commands to verify (not abstract checks)
- Sequential blocking (must pass Agent 1 before Agent 2)
- Mandatory STOP-and-FIX when violations found

