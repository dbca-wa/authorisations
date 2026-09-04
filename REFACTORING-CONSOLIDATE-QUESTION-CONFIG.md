# Refactoring Plan: Consolidate Question Config

**Objective**: Consolidate fragmented question configuration attributes into a unified nested `config` object to improve schema design, reduce API verbosity, and eliminate the TODO marked in `backend/questionnaires/serialisers.py` line 115.

**Status**: Planning phase — awaiting approval before implementation

---

## Executive Summary

### Current Problem
- Five separate question-level fields scattered across question definition:
  - `select_options`: Options for select questions
  - `grid_columns`: Column definitions for grid questions
  - `grid_max_rows`: Maximum rows for grid questions
  - `dependent_step`: Step dependency index for conditional questions
  - `file_max_attachments`: Attachment limit for file questions

- These fields are spread across:
  - Backend Django serializers (flat fields)
  - JSON schema definitions (flat properties)
  - Frontend React TypeScript interfaces (flat properties)
  - Frontend React components (scattered property access)
  - Test fixtures (backend and frontend)

- Inconsistency: There's an uncommented `QuestionExtraAttrs` class in serializers that's never used, and a TODO at line 115 marking this as a future migration

### Desired Outcome
All configuration attributes consolidated into a single nested `config` object:
```python
# Before (flat)
question = {
    "label": "...",
    "type": "...",
    "select_options": [...],
    "grid_columns": [...],
    "grid_max_rows": 10,
    "dependent_step": 1,
    "file_max_attachments": 3,
}

# After (nested)
question = {
    "label": "...",
    "type": "...",
    "config": {
        "select_options": [...],
        "grid_columns": [...],
        "grid_max_rows": 10,
        "dependent_step": 1,
        "file_max_attachments": 3,
    }
}
```

### Benefits
- **Schema clarity**: Core question metadata (label, type, required) separated from type-specific configuration
- **Reduced verbosity**: Nested object is more organized than flat list of fields
- **Future scalability**: New type-specific fields can be added to `config` without bloating question definition
- **API consistency**: Mirrors modern API design patterns (nested configuration objects)
- **Removes technical debt**: Eliminates the TODO and uncommented code

---

## Implementation Strategy

### High-Level Approach

This refactoring requires **coordinated changes across all layers** in a specific sequence:

1. **Schema Migration Framework** — Define transformation from schema v0 (flat) to v1 (nested)
2. **Backend Serializers** — Update API contract to use nested structure
3. **Backend Models & Logic** — Update code that reads question config
4. **Database Migration** — Execute schema migration on questionnaire documents
5. **Frontend Types** — Update TypeScript interfaces
6. **Frontend Components** — Update component property access
7. **Test Coverage** — Ensure all tests pass with new structure
8. **Documentation** — Update architecture and migration docs
9. **Changelog** — Record the consolidation

### Key Constraint: Version Management

- **Current schema version** in `backend/questionnaires/schema.py`: `SCHEMA_VERSION = 0`
- **After refactoring**: `SCHEMA_VERSION = 1`
- **Migration file**: `backend/questionnaires/schema_migrations/0001_consolidate_question_config.py`
  - Transforms: schema_version 0 → 1
  - Transforms: flat extra attributes → nested `config` object
  - Includes forward and backward transforms for rollback safety

---

## Phase-by-Phase Breakdown

### Phase 1: Schema Migration Implementation (Backend)

**Outcome**: New migration that transforms schema v0 → v1

**Files to Create**:
- `backend/questionnaires/schema_migrations/0001_consolidate_question_config.py`
  - `previous_schema()`: Hard-coded snapshot of v0 schema (flat structure)
  - `target_schema()`: Hard-coded snapshot of v1 schema (nested `config` object)
  - `migrate_forward(doc)`: Transforms question documents from flat to nested
  - `migrate_backward(doc)`: Transforms question documents from nested back to flat
  - Comprehensive docstring explaining transformation

**Key Implementation Details**:
- Migration handles questions nested within steps/sections
- Safely handles questions that don't have all config fields (optional fields)
- Creates `config` object only if at least one config field exists
- Empty or missing config fields are preserved (not added if not present)
- Backward migration reconstructs exact original flat structure

**Testing**: Unit tests in `backend/questionnaires/tests/test_schema_migration_0001.py`
- Test forward migration on sample documents
- Test backward migration restores original
- Test edge cases (missing fields, nested fields in grid columns, etc.)
- Test idempotency (migrating twice is same as once)

---

### Phase 2: Schema & Serializer Updates (Backend)

**Outcome**: Updated schema definition and API contract

**Files to Modify**:

#### `backend/questionnaires/serialisers.py`
1. Rename `QuestionExtraAttrs` → `QuestionConfig` (align with new terminology)
2. Update fields inside `QuestionConfig`:
   - `select_options`
   - `grid_columns` (with nested `GridQuestionColumnSerialiser`)
   - `grid_max_rows`
   - `dependent_step`
   - `file_max_attachments`
3. Update `QuestionSerialiser`:
   - Remove flat fields: `select_options`, `grid_columns`, `grid_max_rows`, `dependent_step`, `file_max_attachments`
   - Add: `config = QuestionConfig(required=False, allow_null=False, default=dict())`
   - Update comments to reference `config` instead of `extra_attributes`

#### `backend/questionnaires/schema.py`
1. Update `SCHEMA_VERSION = 0` → `SCHEMA_VERSION = 1`
2. Update `_SCHEMA_QUESTIONNAIRE` in `$defs.question`:
   - Remove flat properties: `select_options`, `grid_columns`, `grid_max_rows`, `dependent_step`, `file_max_attachments`
   - Add nested `config` property with schema definition
   - Update property references in schema comments
3. Example structure in schema:
   ```json
   {
     "config": {
       "type": "object",
       "properties": {
         "select_options": { "type": "array", "items": { "type": "string" } },
         "grid_columns": { "type": "array", "items": { "$ref": "#/$defs/grid_column" } },
         "grid_max_rows": { "type": "integer", "minimum": 1, "maximum": 20 },
         "dependent_step": { "type": "integer", "minimum": 1, "maximum": 10 },
         "file_max_attachments": { "type": "integer", "minimum": 1, "maximum": 20 }
       },
       "additionalProperties": false
     }
   }
   ```

**API Contract Changes**:
- Old endpoint response: question with flat fields
- New endpoint response: question with nested `config` object
- Frontend must update to consume new structure

---

### Phase 3: Backend Code Updates

**Outcome**: All backend code that reads question config works with nested structure

**Files to Modify**:

#### `backend/applications/models.py`
Functions that access question configuration:

1. `_build_grid_rows(question, raw_value)`:
   - Old: `question.get("grid_columns")`
   - New: `question.get("config", {}).get("grid_columns")`

2. `_build_question_item(question, answer_value, ...)`:
   - Old: `question.get("grid_columns")`
   - New: `question.get("config", {}).get("grid_columns")`

#### `backend/applications/serialisers.py`
In `AttachmentSerialiser`:

1. `validate_application_key()` method:
   - Reads `file_max_attachments` from question
   - Old: `question.get("file_max_attachments")`
   - New: `question.get("config", {}).get("file_max_attachments")`

#### `backend/templates/application-pdf-template.html`
- Line 451: Grid column iteration
  - Old: `question.grid_columns`
  - New: `question.config.grid_columns` (already resolved in Python model, no change needed here)

**Testing**: Run backend tests to verify all code paths work
- `cd backend && poetry run pytest`
- Pay special attention to:
  - Grid question rendering
  - File attachment validation
  - Question display in PDF generation

---

### Phase 4: Frontend Type Definitions

**Outcome**: TypeScript interfaces reflect nested config structure

**Files to Modify**:

#### `frontend/src/context/types/Questionnaire.ts`

1. Create new interface `IQuestionConfig`:
```typescript
export interface IQuestionConfig {
  select_options?: string[] | null;
  grid_columns?: IGridQuestionColumn[] | null;
  grid_max_rows?: number | null;
  dependent_step?: number | null;
  file_max_attachments?: number | null;
}
```

2. Update `IQuestion` interface:
```typescript
export interface IQuestion {
  label: string;
  type: string;
  is_required: boolean;
  description?: string;
  config?: IQuestionConfig | null;  // New nested field
  // Remove old flat fields:
  // - select_options ❌
  // - grid_columns ❌
  // - grid_max_rows ❌
  // - dependent_step ❌
  // - file_max_attachments ❌
}
```

3. `IGridQuestionColumn` remains unchanged (nested within grid_columns inside config)

**Verification**: TypeScript compiler should catch any remaining property access issues

---

### Phase 5: Frontend Component Updates

**Outcome**: React components use new nested access pattern

**Files to Modify**:

#### `frontend/src/components/inputs/file.tsx`
- Line ~54: `question.o.file_max_attachments`
  - New: `question.o.config?.file_max_attachments ?? 1`
  - Reason: Optional chaining for null safety, default to 1 if missing

#### `frontend/src/components/inputs/grid.tsx`
- Line ~55: `question.o.grid_columns?.forEach(...)`
  - New: `question.o.config?.grid_columns?.forEach(...)`
- Line ~109: Same pattern
- Line ~241: `(question.o.grid_columns || [])`
  - New: `(question.o.config?.grid_columns || [])`
- Line ~311: Same pattern

#### `frontend/src/components/inputs/select.tsx`
- Line ~39: `{question.o.select_options?.map(...)`
  - New: `{question.o.config?.select_options?.map(...)`

#### `frontend/src/components/layout/form/FormActiveStep.tsx`
- Line ~285: `const walkback = question.o.dependent_step;`
  - New: `const walkback = question.o.config?.dependent_step;`

#### `frontend/src/components/layout/form/FormReviewPage.tsx`
- Line ~345: Grid column iteration
  - Old: `{question.grid_columns?.map(...)`
  - New: `{question.config?.grid_columns?.map(...)`
- Line ~355: Same

**Pattern Used**:
- All property accesses use optional chaining (`?.`) for null safety
- Provide sensible defaults where needed (e.g., `?? 1` for file max attachments)
- No change to component logic, only property access paths

---

### Phase 6: Test Updates & Fixtures

**Outcome**: All tests pass with new nested structure

**Files to Create/Modify**:

#### Backend Tests

**New File**: `backend/questionnaires/tests/test_schema_migration_0001.py`
- Test forward migration (v0 → v1)
- Test backward migration (v1 → v0)
- Test edge cases (missing fields, empty config, nested structures)
- Test idempotency

**Modified Files**:

- `backend/questionnaires/tests/test_models.py`:
  - Update Questionnaire model fixtures to use new schema v1 structure

- `backend/questionnaires/tests/test_serialisers.py`:
  - Update serializer test fixtures
  - Test `QuestionConfig` validation
  - Test nested field validation

- `backend/applications/tests/test_models.py`:
  - Update fixtures that include grid/select/file questions
  - Test `_build_grid_rows()` with nested config access

- `backend/applications/tests/test_serialisers.py`:
  - Update attachment validation tests
  - Test that `file_max_attachments` is read from nested path

- `backend/api/tests/test_*.py` (all API test files):
  - Update question fixtures to use nested config
  - Update assertions on API responses

- `backend/e2e/tests/test_*.py` (if applicable):
  - Update E2E test fixtures
  - Verify full user workflows work

- `backend/e2e/fixtures/e2e_seed.json`:
  - Update seed data to use nested config structure

**Command**: 
```bash
cd backend && poetry run pytest
```

#### Frontend Tests

**Modified Files**:

- `frontend/src/test/unit/fixtures.ts`:
  - Update question fixture factory to generate nested config
  - Ensure all test utilities use new structure

- `frontend/src/test/unit/components/inputs/file-input.test.tsx`:
  - Update test fixtures (line ~77): `file_max_attachments` → `config: { file_max_attachments: 2 }`
  - Update all question fixtures in file

- `frontend/src/test/unit/components/inputs/grid-input.test.tsx`:
  - Update test fixtures (line ~14): `grid_columns` → `config: { grid_columns: [...] }`
  - Update all grid-related assertions

- `frontend/src/test/unit/components/inputs/select-input.test.tsx`:
  - Update test fixtures (line ~14): `select_options` → `config: { select_options: [...] }`

- `frontend/src/test/unit/components/layout/form/form-active-step.test.tsx`:
  - Update test fixtures (line ~108): `dependent_step` → `config: { dependent_step: 1 }`

**Command**:
```bash
cd frontend && npm run test:unit
```

---

### Phase 7: Documentation Updates

**Outcome**: Project documentation reflects new structure

**Files to Modify**:

#### `docs/ARCHITECTURE.md`
- Add section explaining question config consolidation
- Show example of new nested structure
- Explain rationale for consolidation

#### `docs/SCHEMA-MIGRATION-HANDBOOK.md`
- Add section documenting migration 0001
- Show example of forward/backward transforms
- Explain how to run the migration operationally
- Show how rollback works

#### `docs/SCHEMA-MIGRATION-PLAN.md`
- Update "Confirmed Decisions" section
- Document that question config consolidation is complete
- Show completed phases

#### `CHANGELOG.md`
- Add entry under new unreleased version:
  ```markdown
  - Consolidated question configuration attributes (select_options, grid_columns, grid_max_rows, dependent_step, file_max_attachments) into nested `config` object for improved schema clarity and API consistency.
  ```

#### Any other relevant docs
- Search for references to "extra_attributes" and update to "config"
- Remove commented-out code examples referring to old structure

---

## Files Changed Summary

### Backend Changes

| File | Type | Changes |
|------|------|---------|
| `schema_migrations/0001_consolidate_question_config.py` | **NEW** | Migration v0→v1 with forward/backward transforms |
| `serialisers.py` | Modify | Rename/uncomment `QuestionConfig`, remove flat fields from `QuestionSerialiser` |
| `schema.py` | Modify | Update `SCHEMA_VERSION=1`, remove flat properties, add nested `config` property |
| `applications/models.py` | Modify | Update 2-3 functions reading grid_columns, file_max_attachments |
| `applications/serialisers.py` | Modify | Update attachment validation to read from nested config |
| `tests/test_schema_migration_0001.py` | **NEW** | Migration tests (forward, backward, edge cases) |
| `tests/test_models.py` | Modify | Update fixtures to schema v1 |
| `tests/test_serialisers.py` | Modify | Update fixtures, test QuestionConfig |
| `applications/tests/test_models.py` | Modify | Update grid/file fixtures |
| `applications/tests/test_serialisers.py` | Modify | Update attachment tests |
| `api/tests/test_*.py` | Modify | Update API response fixtures |
| `e2e/tests/test_*.py` | Modify | Update E2E fixtures if applicable |
| `e2e/fixtures/e2e_seed.json` | Modify | Update seed questionnaires to v1 |

### Frontend Changes

| File | Type | Changes |
|------|------|---------|
| `context/types/Questionnaire.ts` | Modify | Add `IQuestionConfig`, update `IQuestion`, remove flat fields |
| `components/inputs/file.tsx` | Modify | `question.o.file_max_attachments` → `question.o.config?.file_max_attachments ?? 1` |
| `components/inputs/grid.tsx` | Modify | `question.o.grid_columns` → `question.o.config?.grid_columns` (3 locations) |
| `components/inputs/select.tsx` | Modify | `question.o.select_options` → `question.o.config?.select_options` |
| `components/layout/form/FormActiveStep.tsx` | Modify | `question.o.dependent_step` → `question.o.config?.dependent_step` |
| `components/layout/form/FormReviewPage.tsx` | Modify | `question.grid_columns` → `question.config?.grid_columns` (2 locations) |
| `test/unit/fixtures.ts` | Modify | Update question factory for nested config |
| `test/unit/components/inputs/file-input.test.tsx` | Modify | Update test fixtures |
| `test/unit/components/inputs/grid-input.test.tsx` | Modify | Update test fixtures |
| `test/unit/components/inputs/select-input.test.tsx` | Modify | Update test fixtures |
| `test/unit/components/layout/form/form-active-step.test.tsx` | Modify | Update test fixtures |

### Documentation Changes

| File | Type | Changes |
|------|------|---------|
| `docs/ARCHITECTURE.md` | Modify | Add section on question config structure |
| `docs/SCHEMA-MIGRATION-HANDBOOK.md` | Modify | Document migration 0001 |
| `docs/SCHEMA-MIGRATION-PLAN.md` | Modify | Update completion status |
| `CHANGELOG.md` | Modify | Add consolidation entry |

---

## Testing Strategy

### Backend Testing

**Unit Tests**:
- `test_schema_migration_0001.py`: Test forward/backward migration
- `test_serialisers.py`: Test `QuestionConfig` validation
- `test_models.py`: Test grid/file functions with nested access

**Integration Tests**:
- All app tests: `pytest applications`, `pytest questionnaires`, `pytest api`
- Full suite: `pytest` from backend directory

**Execution**:
```bash
cd backend
poetry run pytest -v
```

### Frontend Testing

**Unit Tests**:
- All component tests with updated fixtures
- Full test suite

**Build Verification**:
```bash
cd frontend
npm run lint
npm run test:unit
npm run build  # Verify no type errors
```

### Quality Assurance

**Type Safety**:
- TypeScript compilation must pass with no errors
- ESLint/linting must pass

**No Breaking Changes**:
- Migration must be reversible (backward migration works)
- Dry-run migration must not modify data

**Manual Verification** (if needed):
- Create a test questionnaire with grid question
- Create a test questionnaire with select question
- Create a test questionnaire with file upload
- Create a test questionnaire with conditional (dependent) question
- Verify all work correctly after refactoring

---

## Deployment & Data Migration

### Deployment Sequence

1. **Pre-Deployment** (in current session):
   - Implement all code changes
   - Pass all unit/integration tests
   - Create schema migration file

2. **Deployment to Staging**:
   - Deploy code changes (now expecting schema v1)
   - Run migration dry-run: `python manage.py schema_migrate --target questionnaires --dry-run 1`
   - Verify dry-run report shows all documents would be migrated
   - Run actual migration: `python manage.py schema_migrate --target questionnaires 1`
   - Verify all questionnaires are now v1
   - Verify application still works

3. **Deployment to Production**:
   - Same sequence as staging
   - Enter maintenance mode before migration
   - Run migration
   - Exit maintenance mode
   - Monitor application behavior

### Rollback (If Needed)

```bash
# Get the migration run_id from the migration report
python manage.py schema_rollback --target questionnaires 0001 --run-id <run_id>
```

---

## Success Criteria

**Before Implementation Starts**:
- [ ] Plan is reviewed and approved by project owner
- [ ] No questions about scope or approach

**During Implementation**:
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] TypeScript compilation succeeds (zero errors)
- [ ] ESLint passes (zero errors)
- [ ] Schema migration file created and tested

**Post-Implementation**:
- [ ] Full test suite passes locally
- [ ] Migration is reversible (backward works)
- [ ] Dry-run on staging shows correct transformation
- [ ] Manual testing of all question types works
- [ ] Documentation is complete and accurate
- [ ] CHANGELOG entry added
- [ ] Code review completed

---

## Terminology Consistency

### Term Mapping (NEW):
- Old term: "extra_attributes" → **New term: "config"**
- Old term: "extra_* fields" → **New term: "config fields"**
- Old term: "QuestionExtraAttrs" → **New term: "QuestionConfig"**

### Where "config" is used:
- Python serializer class: `QuestionConfig`
- Python field name: `config`
- TypeScript interface: `IQuestionConfig`
- TypeScript field name: `config`
- JSON schema property: `"config"`
- Comments and documentation: "question config", "config object", etc.

### Files to clean of old terminology:
- Remove all `extra_attributes` comments
- Remove uncommented `QuestionExtraAttrs` code
- Remove TODO at line 115 of serialisers.py
- Search workspace for remaining "extra_attributes" references
- Search workspace for remaining "extra_attr" references

---

## Risk & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Lost data in migration** | HIGH | Transaction-backed migration with dry-run support; test migration on staging first |
| **Incomplete component updates** | HIGH | Global search for all property names; TypeScript compiler validates |
| **Null pointer errors** | MEDIUM | Use optional chaining (`?.`) in all frontend access; test with null/undefined |
| **Missed test fixtures** | MEDIUM | Run full test suite; any test failure immediately shows missed fixture |
| **Backward migration fails** | MEDIUM | Test backward migration in unit tests; include edge cases |
| **Documentation drift** | LOW | Update docs in same PR; run final doc review |
| **Schema validator issues** | MEDIUM | Test schema with validator in migration file; unit tests verify structure |

---

## Open Questions (For User)

Before we start implementation, please clarify:

1. **Timeline**: Are there any deployment constraints or preferred timeline for this refactoring?
2. **E2E Tests**: Should we add E2E tests for the full questionnaire lifecycle after refactoring?
3. **Deprecation Period**: Do we need a deprecation period for the old flat structure, or is a hard cutover acceptable?
4. **Monitoring**: Are there specific metrics or checks we should monitor post-deployment?
5. **User Documentation**: Do any user-facing docs (external guides, FAQs) need updating for the new structure?

---

## Next Steps

**If approved**:
1. Confirm no open questions
2. Begin Phase 1: Schema Migration Implementation
3. Proceed through phases sequentially
4. Deliver for code review after all phases complete

**If changes needed**:
1. Provide feedback on plan
2. Update plan document
3. Re-review and approve

