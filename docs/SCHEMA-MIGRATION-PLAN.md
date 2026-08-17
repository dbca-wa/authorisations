# Schema Migration Plan

## Objective

Design and deliver a reusable, safe migration framework for both `Questionnaire.document` and `Application.document` that enables schema evolution in a controlled maintenance window. The framework follows Django's migration philosophy: code-based, transaction-backed, with deterministic rollback.

The framework prioritises:
- **data safety** — single transaction atomicity, strict validation before/after
- **operational clarity** — simple command interface, clear error messages
- **strict runtime behaviour** — reject old schema_version with actionable guidance
- **low implementation complexity** — no database state tracking, no backup columns
- **repeatability** — reusable migration pattern for future schema changes
- **safe codebase rollback** — migration files permanently stored in git history; code changes can be reverted independently of data transforms

---

## Confirmed Decisions (Simplified Approach)

- **No backup columns**: Transactions provide atomicity. On failure, entire transaction rolls back. Previous schema definitions kept in git/codebase for emergency rollback.
- **No database state tracking**: Single text file (`.schema_version.txt`) tracks current version. No Django migration table equivalent.
- **Single-version production code**: Only `get_questionnaire_schema()` and `get_answers_schema()` exist; always return current schema.
- **Migrations as code**: Transform functions (`migrate_forward()`, `migrate_backward()`) stored in migration files alongside schema definitions.
- **Migration execution**: Maintenance window + single transaction via management command. Operator activates `MAINTENANCE_MODE` for write blocking.
- **Runtime policy**: Strict current-version-only acceptance. Old data throws clear error directing to migration command.
- **Answer key contracts preserved**: `section-question` (application answers) and `step.section-question` (attachments) formats unchanged.

---

## `.schema_version.txt` Explained

### Purpose

Track the **current schema version** that all records in the database should conform to. Single source of truth for:
- Operators: "Where are we?" (`--status` command reads this)
- Management commands: What version to migrate from/to
- Runtime validation: What version to expect in documents
- Tests: What version fixtures should use
- Git history: When versions changed (commits show diffs)

### Content

Single line per file with version identifier:

```
backend/questionnaires/.schema_version.txt
2025.07-1

backend/applications/.schema_version.txt
2025.09-1
```

### Why Text File (Not Database Table)?

1. **Simplicity**: No database schema overhead. Humans can read/edit if needed.
2. **Django alignment**: Migrations are code files; version is a code fact.
3. **Git-friendly**: Commit history shows when versions changed. Easy rollback: revert commit → revert version file → re-run migration backward.
4. **No deployment complexity**: No need to migrate state tracking schema itself.

### Updated When

- **Migration execute** (e.g., `schema_migrate_questionnaire 0002`): Updated to target version after all transforms succeed in transaction
- **Migration fails**: Entire transaction rolls back; version file unchanged
- **Rollback procedure**: See [Rollback Procedures](#rollback-procedures) section (critical: migration files are never deleted from git; codebase changes are reverted independently)

---

## Scope & Safety Invariants

### In Scope

- Django-inspired migration framework (code-based, no state tracking)
- Simple version tracking via `.schema_version.txt`
- Management commands: `schema_migrate_questionnaire N` (migrate to version N), `schema_rollback_questionnaire N` (rollback to version N), `schema_status_questionnaire` (show current state)
- Transformation pipeline with pre/post validation
- Strict runtime validation (API rejects old schema_version)
- Backward transforms (for safe data rollback)
- Test coverage and operator runbook
- Safe codebase rollback with permanent migration file history

### Out of Scope

- Automatic backup cleanup
- Long-lived dual-version runtime support
- Answer key format redesign
- Admin clone-on-edit changes
- Database migration state tracking table

### Safety Invariants (Must Always Hold)

1. Documents remain structurally valid against target schema after transformation
2. Answer key contracts unchanged: `section-question` (app answers), `step.section-question` (attachments)
3. Runtime strictly rejects `schema_version ≠ current_version`
4. Rollback via transaction rollback + backward transform restores exact original state

---

## Architecture

### 1. Schema Version & Current Getter

**What exists**:
- `backend/questionnaires/schema.py` — `get_questionnaire_schema()` returns current schema
- `backend/applications/schema.py` — `get_answers_schema()` returns current schema

**What we add**:
- `.schema_version.txt` files in each app (version tracking)
- `get_current_schema_version() -> str` function (reads version file)

### 2. Migration File Structure

Each migration file contains four elements:

```python
"""Migration: Brief description of what changes."""

SCHEMA_VERSION = "2025.07-2"  # The version this migration establishes

def previous_schema():
    """Return the previous schema version definition for reference."""
    # Kept in codebase for rollback reference
    pass

def migrate_forward(doc: dict) -> dict:
    """Transform from previous version to SCHEMA_VERSION."""
    # Applied when moving forward
    pass

def migrate_backward(doc: dict) -> dict:
    """Revert from SCHEMA_VERSION to previous version."""
    # Applied when rolling back
    pass
```

**Example**: `backend/questionnaires/schema_migrations/0001_initial.py` (bootstrap)

```python
"""Migration: Bootstrap - establishes baseline schema version 2025.07-1."""

SCHEMA_VERSION = "2025.07-1"

def previous_schema():
    """No previous schema; this is the baseline."""
    from questionnaires.schema import get_questionnaire_schema
    return get_questionnaire_schema()

def migrate_forward(doc: dict) -> dict:
    """Identity transform (already at baseline)."""
    return doc

def migrate_backward(doc: dict) -> dict:
    """Identity transform (already at baseline)."""
    return doc
```

**Example**: `backend/questionnaires/schema_migrations/0002_extra_attributes_consolidation.py` (real change)

```python
"""Migration: Consolidate question extra_* fields into single extra_attributes object."""

SCHEMA_VERSION = "2025.07-2"

def previous_schema():
    """Return 2025.07-1 schema definition (old flat structure)."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "default": "2025.07-1"},
            "steps": {"type": "array", "items": {"$ref": "#/$defs/step"}},
        },
        # ... (rest of old schema)
    }

def migrate_forward(doc: dict) -> dict:
    """Transform: flat extra_* fields → extra_attributes object."""
    if doc.get("schema_version") != "2025.07-1":
        raise ValueError(
            f"Expected schema 2025.07-1, got {doc.get('schema_version')}"
        )
    
    doc = doc.copy()
    doc["schema_version"] = "2025.07-2"
    
    # Transform each question in each section of each step
    for step in doc.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                # Extract flat extra_* fields
                extra_attrs = {}
                for field in [
                    "select_options",
                    "grid_columns",
                    "grid_max_rows",
                    "dependent_step",
                    "file_max_attachments",
                ]:
                    if field in question:
                        extra_attrs[field] = question.pop(field)
                
                # Add consolidated object only if any attributes exist
                if extra_attrs:
                    question["extra_attributes"] = extra_attrs
    
    return doc

def migrate_backward(doc: dict) -> dict:
    """Transform: extra_attributes object → flat extra_* fields."""
    if doc.get("schema_version") != "2025.07-2":
        raise ValueError(
            f"Expected schema 2025.07-2, got {doc.get('schema_version')}"
        )
    
    doc = doc.copy()
    doc["schema_version"] = "2025.07-1"
    
    # Expand extra_attributes back to flat fields
    for step in doc.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                extra_attrs = question.pop("extra_attributes", {})
                if extra_attrs:
                    question.update(extra_attrs)
    
    return doc
```

### 3. Migration Loader & Path Resolution

**File**: `backend/questionnaires/schema_migrations_loader.py`

Discovers and imports migration files; resolves transformation chains:

```python
"""Load migration files and resolve transformation paths."""

def get_migration(version: str):
    """Load and return migration module for version."""
    # Dynamically import schema_migrations.00XX_*.py by SCHEMA_VERSION
    pass

def list_migrations() -> list[str]:
    """Return all available migration versions in order."""
    # Scan schema_migrations/ directory, extract SCHEMA_VERSION from each
    pass

def find_path(from_version: str, to_version: str) -> list[str]:
    """Find transformation path between versions."""
    # Example: find_path("2025.07-1", "2025.07-2") → ["2025.07-1", "2025.07-2"]
    # Example: find_path("2025.07-2", "2025.07-1") → ["2025.07-2", "2025.07-1"]
    pass
```

### 4. Migration Validation Utility

**File**: `backend/questionnaires/schema_migration_utils.py`

Validates transforms before applying:

```python
"""Validate schema transforms."""

def validate_transform(
    doc: dict, from_version: str, to_version: str
) -> tuple[bool, list[str]]:
    """
    Validate that transform produces valid output.
    
    Returns: (is_valid: bool, errors: list[str])
    """
    # Load migration, apply transform, validate against schema
    pass
```

### 5. Management Command Interface

**Files**:
- `backend/questionnaires/management/commands/schema_migrate_questionnaire.py` — Migrate questionnaires forward
- `backend/questionnaires/management/commands/schema_rollback_questionnaire.py` — Rollback questionnaires to previous version
- `backend/questionnaires/management/commands/schema_status_questionnaire.py` — Show current version and distribution
- Same three commands for applications (with `schema_migrate_application`, `schema_rollback_application`, `schema_status_application`)

**Command syntax** (following Django's `migrate` command pattern):

```bash
# Show current version and record distribution
python manage.py schema_status_questionnaire
# Output:
# Current schema version: 2025.07-1
#   2025.07-1: 147 questionnaires
# Available migrations: 0001, 0002, 0003

# Dry run: test transform to specific migration number, no writes
python manage.py schema_migrate_questionnaire 0002 --dry-run
# Output:
# Found 147 questionnaires at version 2025.07-1
# DRY RUN: Would migrate to schema version 2025.07-2...
# Would transform 147/147 successfully

# Actually migrate to specific migration number
python manage.py schema_migrate_questionnaire 0002
# Output:
# Found 147 questionnaires at version 2025.07-1
# Migrating to schema version 2025.07-2...
# ✓ Migrated 147/147 questionnaires. Updated .schema_version.txt to 2025.07-2

# Rollback to previous migration (backward)
python manage.py schema_rollback_questionnaire 0001
# Output:
# Found 147 questionnaires at version 2025.07-2
# Rolling back to schema version 2025.07-1...
# ✓ Rolled back 147/147 questionnaires. Updated .schema_version.txt to 2025.07-1
```

**Command argument semantics**:
- Argument is migration **number** (e.g., `0002`), not version string
- Loader resolves number → finds migration file → reads SCHEMA_VERSION from file
- Forward direction: current version → target version (all migrations between applied in order)
- Backward direction: current version → target version (all migrations between reversed in order)

---

## Implementation Phases (Detailed & Actionable)

### Phase 1: Schema Version Tracking (~2 hours)

**What to do**:

1. Create `.schema_version.txt` files:
   ```
   echo "2025.07-1" > backend/questionnaires/.schema_version.txt
   echo "2025.09-1" > backend/applications/.schema_version.txt
   ```

2. Add `get_current_schema_version()` function to both schema modules (imports at module level per FEATURE-DEVELOPMENT.md):
   ```python
   # At module level (top of file)
   import os
   
   def get_current_schema_version() -> str:
       """Read and return current schema version from .schema_version.txt."""
       version_file = os.path.join(os.path.dirname(__file__), ".schema_version.txt")
       with open(version_file) as f:
           return f.read().strip()
   ```

3. Create migration directories:
   ```
   mkdir -p backend/questionnaires/schema_migrations
   touch backend/questionnaires/schema_migrations/__init__.py
   mkdir -p backend/applications/schema_migrations
   touch backend/applications/schema_migrations/__init__.py
   ```

4. Add version comments to schema modules (e.g., `backend/questionnaires/schema.py#L15`):
   ```python
   # Current schema version: 2025.07-1
   # Previous versions are maintained in schema_migrations/ directory
   ```

**Tests to write**:
- `backend/questionnaires/tests/test_schema_version.py` — Verify `get_current_schema_version()` returns correct value
- `backend/applications/tests/test_schema_version.py` — Same

**Exit criteria**:
- ✓ Version files exist and readable
- ✓ `get_current_schema_version()` works for both modules
- ✓ Migration directories exist and importable

---

### Phase 2: Runtime Schema Validation (Strict Mode) (~3 hours)

**What to do**:

1. Update `ApplicationSerialiser.validate_document()` in `backend/applications/serialisers.py` (~line 321-328). Import at module level:
   ```python
   # At module level (top of file)
   from applications.schema import get_current_schema_version
   
   # In the validate_document method:
   def validate_document(self, value):
       current_version = get_current_schema_version()
       doc_version = value.get("schema_version") if isinstance(value, dict) else None
       
       if doc_version != current_version:
           raise serializers.ValidationError(
               f"Document schema version must be '{current_version}', but got '{doc_version}'. "
               f"Run migration: python manage.py schema_migrate_application {current_version}"
           )
       
       schema = get_answers_schema()
       return self._validate_document(value, schema)
   ```

2. Update `QuestionnaireSerialiser.validate_document()` in `backend/questionnaires/models.py` (~line 127-134). Import at module level:
   ```python
   # At module level (top of file)
   from questionnaires.schema import get_current_schema_version
   
   # In the validate_document method:
   def validate_document(self, value):
       current_version = get_current_schema_version()
       doc_version = value.get("schema_version") if isinstance(value, dict) else None
       
       if doc_version != current_version:
           raise serializers.ValidationError(
               f"Document schema version must be '{current_version}', but got '{doc_version}'. "
               f"Run migration: python manage.py schema_migrate_questionnaire {current_version}"
           )
       
       schema = get_questionnaire_schema()
       return self._validate_document(value, schema)
   ```

**Tests to write**:
- `backend/api/tests/test_application_serializer_strict_version.py` — Reject old schema_version
- `backend/questionnaires/tests/test_questionnaire_strict_version.py` — Same

**Exit criteria**:
- ✓ API rejects documents with mismatched schema_version
- ✓ Error messages guide to migration command
- ✓ Existing tests pass

---

### Phase 3: Migration File Infrastructure (~4 hours)

**What to do**:

1. Create `backend/questionnaires/schema_migrations_loader.py` and `backend/applications/schema_migrations_loader.py` with:
   - `get_migration(version: str)` — Import migration module by version
   - `list_migrations() -> list[str]` — List all available versions in order
   - `find_path(from_version, to_version) -> list[str]` — Resolve version chain

2. Create `backend/questionnaires/schema_migration_utils.py` and `backend/applications/schema_migration_utils.py` with:
   - `validate_transform(doc, from_version, to_version) -> (bool, list[str])` — Validate transform output

3. Create bootstrap migration files `0001_initial.py` in each app (identity transform, establishes baseline)

**Tests to write**:
- `backend/questionnaires/tests/test_schema_migrations_loader.py` — Test listing, path finding
- `backend/applications/tests/test_schema_migrations_loader.py` — Same

**Exit criteria**:
- ✓ Migration loader finds and lists migrations
- ✓ Path finding works forward/backward
- ✓ Validation applies transforms correctly

---

### Phase 4: Management Commands (~6 hours)

**What to do**:

1. Create three command files for questionnaires:
   - `backend/questionnaires/management/commands/schema_migrate_questionnaire.py`
   - `backend/questionnaires/management/commands/schema_rollback_questionnaire.py`
   - `backend/questionnaires/management/commands/schema_status_questionnaire.py`

2. Create identical three commands for applications:
   - `backend/applications/management/commands/schema_migrate_application.py`
   - `backend/applications/management/commands/schema_rollback_application.py`
   - `backend/applications/management/commands/schema_status_application.py`

**Command implementation details**:

- **Arguments**: Migration number only (e.g., `0002`), not version strings. Loader maps number → migration file → reads SCHEMA_VERSION
- **Forward migrate**: Applies all forward transforms from current version to target version in a single transaction
- **Backward migrate** (rollback): Applies all backward transforms from current version to target version in a single transaction
- **Status**: Lists current version, shows record distribution by schema_version, lists available migration numbers
- **Dry-run option** (`--dry-run`): Tests transforms without writing; only valid with migrate/rollback, not with status
- **Single transaction**: All records transformed within one database transaction; fail-fast on first error with clear error message showing which record failed
- **Atomic version update**: `.schema_version.txt` updated to target version **only after** all transforms succeed and transaction commits. On failure, entire transaction rolls back and version file unchanged.

**Tests to write**:
- `backend/questionnaires/tests/test_schema_migrate_command.py` — Test migrate forward with/without dry-run
- `backend/questionnaires/tests/test_schema_rollback_command.py` — Test rollback with/without dry-run
- `backend/questionnaires/tests/test_schema_status_command.py` — Test status output
- Same for applications

**Exit criteria**:
- ✓ All commands parse arguments correctly
- ✓ Dry-run produces zero database changes
- ✓ Migrate/rollback update `.schema_version.txt` correctly
- ✓ Transaction rollback on any transform error
- ✓ Error messages identify which record failed and why

---

### Phase 5: Fixtures & Test Data (~2 hours)

**What to do**:

1. Verify existing fixtures in `backend/conftest.py`, `backend/api/tests/conftest.py`, `frontend/src/test/unit/fixtures.ts` already use current schema versions

2. Create migration test fixtures (e.g., `backend/questionnaires/tests/fixtures.py`):
   - Sample documents at old versions (for testing transforms)

**Tests to write**:
- Minimal verification that fixtures use current schemas

**Exit criteria**:
- ✓ Fixtures verified at current versions
- ✓ Old-version test fixtures created for command tests

---

### Phase 6: Integration Tests & Documentation (~4 hours)

**What to do**:

1. Create integration tests:
   - `backend/questionnaires/tests/test_migration_integration.py` — Full lifecycle: create old-version record → migrate → verify
   - `backend/applications/tests/test_migration_integration.py` — Same

2. Update documentation:
   - **`docs/DEPLOYMENT.md`** — Add "Schema Migrations" section with operator runbook:
     ```markdown
     ## Schema Migrations

     ### Operator Workflow

     1. **Check current status**:
        python manage.py schema_status_questionnaire

     2. **Enter maintenance mode** (blocks writes):
        Set MAINTENANCE_MODE=True in settings or environment

     3. **Dry run** (test, no writes):
        python manage.py schema_migrate_questionnaire 0002 --dry-run

     4. **Migrate**:
        python manage.py schema_migrate_questionnaire 0002

     5. **Verify post-migration**:
        python manage.py schema_status_questionnaire
        # Should show all records at new version

     6. **Exit maintenance mode** (re-enable writes)

     ### Rollback (if needed) — See SCHEMA-MIGRATION-PLAN.md section

     Complete rollback procedures are documented in the schema migration plan. Rollback involves three steps:
     1. Execute data rollback command: `python manage.py schema_rollback_questionnaire 0001`
     2. Git revert codebase changes that depend on new schema
     3. Keep migration files in git (never delete them; they're part of permanent history)
     ```

   - **`docs/BACKEND-CONVENTIONS.md`** — Add "JSON Schema Migrations" section explaining:
     - Where migration files live and their structure
     - How to write `migrate_forward()` and `migrate_backward()`
     - How previous schema is kept in migration files for reference
     - Import guidelines: All imports must be at module level per FEATURE-DEVELOPMENT.md

   - **`docs/TESTING.md`** — Add migration testing patterns

**Exit criteria**:
- ✓ Integration tests pass full lifecycle
- ✓ Operator runbook is clear and actionable
- ✓ Developer guide explains writing future migrations

---

## Example: Extra Attributes Consolidation Migration

This section demonstrates applying the framework to the real first schema change.

### Current State (Schema 2025.07-1)

Questions have flat extra fields in [backend/questionnaires/serialisers.py](backend/questionnaires/serialisers.py#L98-L135):

```json
{
  "schema_version": "2025.07-1",
  "steps": [{
    "sections": [{
      "questions": [{
        "label": "Select Question",
        "type": "select",
        "is_required": false,
        "select_options": ["A", "B", "C"],
        "grid_columns": null,
        "grid_max_rows": null,
        "dependent_step": null,
        "file_max_attachments": null
      }]
    }]
  }]
}
```

### Target State (Schema 2025.07-2)

Consolidate into single `extra_attributes` object:

```json
{
  "schema_version": "2025.07-2",
  "steps": [{
    "sections": [{
      "questions": [{
        "label": "Select Question",
        "type": "select",
        "is_required": false,
        "extra_attributes": {
          "select_options": ["A", "B", "C"],
          "grid_columns": null,
          "grid_max_rows": null,
          "dependent_step": null,
          "file_max_attachments": null
        }
      }]
    }]
  }]
}
```

### Migration Implementation

**Step 1**: Create migration file `backend/questionnaires/schema_migrations/0002_extra_attributes_consolidation.py` (see Architecture section above for full code)

**Step 2**: Update serializer in `backend/questionnaires/serialisers.py`:
- Remove commented-out `QuestionExtraAttrs` (uncomment and activate)
- Remove individual `select_options`, `grid_columns`, `grid_max_rows`, `dependent_step`, `file_max_attachments` fields from `QuestionSerialiser`
- Add `extra_attributes = QuestionExtraAttrs(required=False, allow_null=True, default=None)`

**Step 3**: Update JSON schema in `backend/questionnaires/schema.py` — add `extra_attributes` property to question definition

**Step 4**: Update frontend types in `frontend/src/context/types/Questionnaire.ts`:
```typescript
export interface IQuestion {
    label: string;
    type: string;
    is_required?: boolean;
    description?: string;
    extra_attributes?: {
        select_options?: string[];
        grid_columns?: IGridQuestionColumn[];
        grid_max_rows?: number;
        dependent_step?: number;
        file_max_attachments?: number;
    };
}
```

**Step 5**: Execute migration:
```bash
# Check status
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-1
#         2025.07-1: 147 questionnaires
#         Available migrations: 0001, 0002, 0003

# Dry run
python manage.py schema_migrate_questionnaire 0002 --dry-run
# Output: Found 147 questionnaires at version 2025.07-1
#         DRY RUN: Would migrate to schema version 2025.07-2...
#         Would transform 147/147 successfully

# Migrate
python manage.py schema_migrate_questionnaire 0002
# Output: Found 147 questionnaires at version 2025.07-1
#         Migrating to schema version 2025.07-2...
#         ✓ Migrated 147/147 questionnaires. Updated .schema_version.txt to 2025.07-2

# Verify
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-2
#         2025.07-2: 147 questionnaires
#         Available migrations: 0001, 0002, 0003
```

---

## Understanding Migration Files

### What does `0001_initial.py` represent?

`0001_initial.py` is the **baseline bootstrap migration** that establishes the initial schema version. It is **not** a migration from one schema to another; it simply records "this is the current state we're starting from."

**Key characteristics**:
- `SCHEMA_VERSION = "2025.07-1"` (or current baseline version)
- `migrate_forward()` is an **identity transform** (returns the document unchanged)
- `migrate_backward()` is an **identity transform** (no previous version to revert to)
- `previous_schema()` returns the current schema definition (for reference)
- Added to git during Phase 1
- Serves as the anchor point for all future migrations

**Why this design?**
- Establishes a permanent record in the migration file system that version 2025.07-1 is our baseline
- Enables operators to run `schema_migrate_questionnaire 0001` without error (idempotent at baseline)
- Provides consistent migration infrastructure from day one (all versions, including baseline, are tracked in `schema_migrations/`)

### How to implement new migrations

**When to create a migration**: Every schema change (adding fields, restructuring objects, renaming keys, changing constraints) requires a migration file.

**Step-by-step migration implementation**:

1. **Plan the change**: Document what's being removed, added, or restructured in the document JSON structure.

2. **Create the migration file**: Name it `000N_description.py` (increment the number).

3. **Implement `SCHEMA_VERSION`**: Set to the **new** version string your migration establishes (e.g., `"2025.07-2"`).

4. **Implement `previous_schema()`**: Return the schema definition **before** your migration. This is purely for reference and rollback context; it doesn't need to parse anything—just return the old schema dict.

5. **Implement `migrate_forward(doc: dict) -> dict`**:
   - Check that `doc.get("schema_version")` matches the **previous** version (e.g., `"2025.07-1"`). Raise `ValueError` if mismatch.
   - Make a copy of the document: `doc = doc.copy()` (avoid mutating input)
   - Apply your transformation logic (add/remove/restructure fields)
   - Update `doc["schema_version"]` to your new version
   - Return the transformed document
   - **Guideline**: Import all dependencies at module level; transformations should be simple, readable logic (loops, conditionals, basic dict/list operations)

6. **Implement `migrate_backward(doc: dict) -> dict`**:
   - Mirror the forward transform in reverse
   - Check that `doc.get("schema_version")` matches your **new** version. Raise `ValueError` if mismatch.
   - Undo the forward changes (restore removed fields, flatten consolidated objects, etc.)
   - Update `doc["schema_version"]` back to the previous version
   - Return the un-transformed document

7. **Test the migration**:
   - Create test fixtures with documents at the previous version
   - Apply `migrate_forward()` to each, verify against current schema
   - Apply `migrate_backward()` to each, verify they match original state
   - Test edge cases: missing fields, null values, empty collections

8. **Example structure**:
   ```python
   \"\"\"Migration: Consolidate question fields into extra_attributes.\"\"\"
   
   # Module-level imports (per FEATURE-DEVELOPMENT.md)
   from copy import deepcopy
   from questionnaires.schema import get_questionnaire_schema
   
   SCHEMA_VERSION = "2025.07-2"
   
   def previous_schema():
       \"\"\"Return 2025.07-1 schema definition for reference.\"\"\"
       return { ... }  # Old schema dict
   
   def migrate_forward(doc: dict) -> dict:
       \"\"\"Consolidate flat fields into extra_attributes object.\"\"\"
       if doc.get("schema_version") != "2025.07-1":
           raise ValueError(f"Expected 2025.07-1, got {doc.get('schema_version')}")
       
       doc = deepcopy(doc)
       doc["schema_version"] = "2025.07-2"
       
       # Apply transformation logic
       for step in doc.get("steps", []):
           for section in step.get("sections", []):
               for question in section.get("questions", []):
                   # Your specific changes here
                   pass
       
       return doc
   
   def migrate_backward(doc: dict) -> dict:
       \"\"\"Undo consolidation: expand extra_attributes back to flat fields.\"\"\"
       if doc.get("schema_version") != "2025.07-2":
           raise ValueError(f"Expected 2025.07-2, got {doc.get('schema_version')}")
       
       doc = deepcopy(doc)
       doc["schema_version"] = "2025.07-1"
       
       # Reverse transformation logic
       for step in doc.get("steps", []):
           for section in step.get("sections", []):
               for question in section.get("questions", []):
                   # Your specific reverse changes here
                   pass
       
       return doc
   ```

---

## Rollback Procedures

Rollback is a **three-step process** that safely reverts both data and codebase while preserving migration file history. Migration files are **never deleted**; they remain in git as permanent historical record.

### Complete Rollback Workflow

**Scenario**: You've deployed migration 0002 to production, but it causes an issue. You need to revert to 0001.

**Step 1: Rollback the Data**

Execute the rollback command in maintenance mode:

```bash
# Enter maintenance mode first (blocks writes)
export MAINTENANCE_MODE=True

# Verify current state
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-2
#         2025.07-2: 147 questionnaires

# Rollback data to previous version (applies migrate_backward transforms)
python manage.py schema_rollback_questionnaire 0001
# Output: Found 147 questionnaires at version 2025.07-2
# Rolling back to schema version 2025.07-1...
# ✓ Rolled back 147/147 questionnaires. Updated .schema_version.txt to 2025.07-1

# Verify rollback succeeded
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-1
#         2025.07-1: 147 questionnaires
```

**Result**: Data is now at 2025.07-1 schema version. The `.schema_version.txt` file has been updated. All documents pass validation against 2025.07-1 schema.

**Step 2: Revert Codebase Changes**

The codebase (serializers, schema definitions, frontend types) was updated to expect the new schema version. You must revert **only the code changes**, **not the migration file**.

```bash
# Identify the commit range that introduced the new schema changes
git log --oneline | head -20

# Revert the commits that changed serializers, schema.py, frontend types, etc.
# DO NOT use 'git reset' or 'git revert' on the migration file itself
git revert <commit-hash-of-schema-change>

# Verify the revert
git diff HEAD~1 backend/questionnaires/serialisers.py
# Should show the old flat fields are back, extra_attributes consolidation is gone
```

**What to revert**:
- Serializer changes (e.g., uncommenting `QuestionExtraAttrs` → recomment it)
- JSON schema changes in `schema.py` (restore old field definitions)
- Frontend type changes (e.g., restore old `IQuestion` interface)
- Any API or business logic that depends on new schema structure

**What NOT to revert**:
- ❌ Do NOT delete or revert `schema_migrations/0002_extra_attributes_consolidation.py`
- ❌ Do NOT revert Phase 1-4 infrastructure (migration loader, commands, etc.)
- ❌ Do NOT delete `.schema_version.txt` or revert its content to non-existent values

**Why keep migration files?**
Migration files are historical records. Deleting them means:
- You lose the ability to migrate forward again without recreating the file
- Git history becomes incomplete
- Future rollbacks might re-apply the same change without the migration logic

**Step 3: Verify Safe State & Exit Maintenance**

```bash
# Verify codebase is at old version
python manage.py schema_status_questionnaire
# Should show: Current schema version: 2025.07-1

# Run tests to ensure old schema is compatible with reverted code
cd backend && poetry run pytest questionnaires/tests/test_questionnaire_strict_version.py -v

# If tests pass, exit maintenance mode
unset MAINTENANCE_MODE
# Or: Set MAINTENANCE_MODE=False in environment
```

### Recovering from Rollback (Re-migration)

If you've fixed the issues and want to migrate forward again:

```bash
# Schema migration files are intact in git (you never deleted them)
# Simply run migrate command again
python manage.py schema_migrate_questionnaire 0002
# Output: Found 147 questionnaires at version 2025.07-1
#         Migrating to schema version 2025.07-2...
#         ✓ Migrated 147/147 questionnaires. Updated .schema_version.txt to 2025.07-2
```

The migration files are **reusable** because they live permanently in git history.

### Key Invariants (Must Always Hold)

1. **Migration files are immutable history**: Once committed to git, migration files should never be modified or deleted. They're the permanent audit trail.
2. **Codebase changes are independent**: Code changes (serializers, schema.py, frontend types) can be reverted without affecting migration files.
3. **Data rollback is reversible**: If you rollback data via `schema_rollback_questionnaire 0001`, you can re-migrate via `schema_migrate_questionnaire 0002` (migrations are idempotent).
4. **Version file is source of truth**: After any migration or rollback, `.schema_version.txt` reflects the actual version all records should be at. It's the operator's record of "where are we now?"

---

## Verification & Testing

### Automated Tests (All Phases)

- ✓ Phase 1: Version file readable, getter works
- ✓ Phase 2: API rejects mismatched schema_version with actionable error
- ✓ Phase 3: Migration loader finds/lists/resolves paths correctly
- ✓ Phase 4: Command modes all work; dry-run produces zero writes; migrate updates version file
- ✓ Phase 5: Old-version test fixtures created and valid
- ✓ Phase 6: Integration test passes full lifecycle (create old → migrate → verify API strict mode)

### Operator Verification (Pre-Production)

1. **Check status**: `schema_status_questionnaire` shows expected version distribution
2. **Dry run succeeds**: `schema_migrate_questionnaire 0002 --dry-run` completes without writes
3. **Migrate succeeds**: All records transform successfully; version file updated
4. **API enforcement**: Old-version documents rejected with clear error message
5. **Rollback rehearsal**: Execute `schema_rollback_questionnaire 0001`; verify all records revert; then re-migrate forward

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Old data reaches API | Strict version check in serializers; actionable error message guides to migration command |
| Migration corrupts data | Single transaction atomicity; validate before/after; fail-fast on first error |
| Operator confusion | Simple command syntax; error messages suggest next steps; status shows current state |
| Key contract drift | Formats preserved (section-question, step.section-question); regression tests enforce |
| Production downtime | Use MAINTENANCE_MODE; single transaction keeps lock time minimal |
| Lost migration history | Migration files kept in git; can restore old schema via git checkout + re-run backward |
| Accidental version downgrade | Version file is source of truth; only update after successful transaction |

---

## File Deliverables

### Phase 1: Version Tracking
- `.schema_version.txt` (questionnaires, applications)
- `schema.py` updates (version comment, getter function)
- `schema_migrations/` directories

### Phase 2: Runtime Validation
- `serialisers.py` (applications) — version check
- `models.py` (questionnaires) — version check

### Phase 3: Migration Infrastructure
- `schema_migrations_loader.py` (questionnaires, applications)
- `schema_migration_utils.py` (questionnaires, applications)
- `schema_migrations/0001_initial.py` (questionnaires, applications)

### Phase 4: Commands
- `management/commands/migrate_questionnaire_schema.py`
- `management/commands/migrate_application_schema.py`

### Phase 5: Test Data
- `tests/fixtures.py` (questionnaires, applications)

### Phase 6: Documentation & Integration Tests
- `docs/DEPLOYMENT.md` — Schema migration section
- `docs/BACKEND-CONVENTIONS.md` — Schema migration guidelines
- `docs/TESTING.md` — Migration testing patterns
- `tests/test_migration_integration.py` (questionnaires, applications)

### For Extra Attributes Consolidation Specifically
- `schema_migrations/0002_extra_attributes_consolidation.py`
- Updated `serialisers.py` (consolidate to `extra_attributes`)
- Updated `schema.py` (JSON schema with extra_attributes)
- Updated `frontend/src/context/types/Questionnaire.ts`

---

## Conclusion

This simplified framework mirrors Django's migration philosophy: migrations are code files stored in the repository, version is tracked in a simple text file, and operations are deterministic and reversible via transaction atomicity and backward transforms. It enables safe, repeatable schema evolution without significant complexity overhead.
