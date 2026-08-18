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

**Implementation Strategy**: Phase framework implemented first for `questionnaires` module only. Once the framework is proven reliable and well-tested, the same patterns will be applied to `applications` module.

---

## Confirmed Decisions (Simplified Approach)

- **No backup columns**: Transactions provide atomicity. On failure, entire transaction rolls back. Previous schema definitions kept in git/codebase for emergency rollback.
- **No database state tracking**: Single text file (`.schema_version.txt`) ~~tracks current version~~ (**Updated**: Python constant in schema module tracks current version. Simpler, no file I/O required).
- **Single-version production code**: Only `get_questionnaire_schema()` and `get_answers_schema()` exist; always return current schema.
- **Migrations as code**: Transform functions (`migrate_forward()`, `migrate_backward()`) stored in migration files alongside schema definitions.
- **Migration execution**: Maintenance window + single transaction via management command. Operator activates `MAINTENANCE_MODE` for write blocking.
- **Runtime policy**: Strict current-version-only acceptance. Old data throws clear error directing to migration command.
- **Answer key contracts preserved**: `section-question` (application answers) and `step.section-question` (attachments) formats unchanged.

---

## `.schema_version.txt` Explained

### **UPDATED: Schema Version as Python Constant**

**Previous design** (text file `.schema_version.txt`) has been simplified:

- **Current implementation**: Schema version is a Python constant `SCHEMA_VERSION` in `backend/questionnaires/schema.py`
- **Reason**: No file I/O required, no text file delivery concerns, simpler to import and use
- **Location**: `backend/questionnaires/schema.py#L11`:
  ```python
  SCHEMA_VERSION = "2025.07-1"
  ```
- **Usage**: Import directly:
  ```python
  from questionnaires.schema import SCHEMA_VERSION
  ```

### Purpose

Track the **current schema version** that all records in the database should conform to. Single source of truth for:
- Operators: "Where are we?" (from `schema_status_questionnaire` command)
- Management commands: What version is current in the codebase
- Runtime validation: What version to expect in documents
- Tests: What version fixtures should use
- Git history: When versions changed (commits show diffs in constant)

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

**Example**: `backend/questionnaires/schema_migrations/0001_initial.py` (versioning baseline transition)

```python
"""Migration 0001: Versioning baseline transition (2025.07-1 → 1).

Transforms existing questionnaires from calendar-based versioning to ordinal versioning.
This is the first official migration and establishes version "1" as the anchor point
for all future schema changes.

Note: The migration command checks current DB version before running this migration.
This ensures idempotency: running the same migration twice is a safe no-op.
"""

from copy import deepcopy

SCHEMA_VERSION = "1"  # Ordinal versioning starts here


def previous_schema():
    """Return the schema structure under calendar version 2025.07-1 for reference."""
    from questionnaires.schema import get_questionnaire_schema
    # Schema structure is identical; only version number differs
    return get_questionnaire_schema()


def migrate_forward(doc: dict) -> dict:
    """Transform: calendar versioning (2025.07-1) → ordinal versioning (1).
    
    Precondition: This function is called only when document.schema_version == "2025.07-1".
    The management command verifies this before calling migrate_forward().
    """
    if doc.get("schema_version") != "2025.07-1":
        raise ValueError(
            f"Expected schema_version 2025.07-1, got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = "1"
    return doc


def migrate_backward(doc: dict) -> dict:
    """Transform: ordinal versioning (1) → calendar versioning (2025.07-1).
    
    Rollback support: restores documents to pre-migration state.
    """
    if doc.get("schema_version") != "1":
        raise ValueError(
            f"Expected schema_version 1, got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = "2025.07-1"
    return doc
```

**Example**: `backend/questionnaires/schema_migrations/0002_extra_attributes_consolidation.py` (real change)

```python
"""Migration 0002: Consolidate question extra_* fields into extra_attributes object (1 → 2).

Note: The migration command checks current DB version before running.
This ensures idempotency: running twice is safe (first time transforms, second time skips).
"""

from copy import deepcopy

SCHEMA_VERSION = "2"

def previous_schema():
    """Return schema definition for version 1 (old flat structure)."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "string", "default": "1"},
            "steps": {"type": "array", "items": {"$ref": "#/$defs/step"}},
        },
        # ... (rest of schema structure)
    }

def migrate_forward(doc: dict) -> dict:
    """Transform: flat extra_* fields → extra_attributes object (1 → 2).
    
    Precondition: This function is called only when document.schema_version == "1".
    The management command verifies this before calling migrate_forward().
    """
    if doc.get("schema_version") != "1":
        raise ValueError(
            f"Expected schema_version 1, got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = "2"
    
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
    """Transform: extra_attributes object → flat extra_* fields (2 → 1).
    
    Rollback support: restores documents to pre-migration state.
    """
    if doc.get("schema_version") != "2":
        raise ValueError(
            f"Expected schema_version 2, got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = "1"
    
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

### Phase 1: Schema Version Tracking (~2 hours) ✅ COMPLETED

**Implementation Status**: Phase 1 is complete for `questionnaires` module.

**What was done**:

1. ✅ Added `SCHEMA_VERSION` Python constant to `backend/questionnaires/schema.py` using pure ordinal format:
   ```python
   # Current version of the schema (pure ordinal: 1, 2, 3, ...)
   # Previous versions are maintained in schema_migrations/ directory
   SCHEMA_VERSION = "1"
   ```

2. ✅ Created migration directories:
   ```
   mkdir -p backend/questionnaires/schema_migrations
   touch backend/questionnaires/schema_migrations/__init__.py
   ```

3. ✅ Added version comments to schema module

**Why Python constant instead of text file?**
- No file I/O required at runtime
- Imported directly: `from questionnaires.schema import SCHEMA_VERSION`
- No file delivery concerns (text files may not be included in deployments)
- Simpler to test and reason about
- Git history shows version changes in commits

**Exit criteria** (met):
- ✓ Schema version tracked as Python constant
- ✓ Constant importable from schema module
- ✓ Migration directories created
- ✓ No custom file reading function needed

---

### Phase 2: Runtime Schema Validation (Strict Mode) ✅ COMPLETED

**Implementation Status**: Phase 2 is complete for `questionnaires` module.

**What was done**:

1. ✅ Updated `QuestionnaireSerialiser.validate_document()` in `backend/questionnaires/models.py` (lines 129-140):
   ```python
   def validate_document(self, value):
       doc_version = value.get("schema_version") if isinstance(value, dict) else None

       if doc_version != SCHEMA_VERSION:
           raise serializers.ValidationError(
               f"Document schema version must be '{SCHEMA_VERSION}', but got '{doc_version}'. "
               f"Run migration: python manage.py schema_migrate_questionnaire {SCHEMA_VERSION}"
           )

       # Validate and return with the JSON schema
       schema = get_questionnaire_schema()
       return self._validate_document(value, schema)
   ```

2. ✅ Imports at module level:
   ```python
   from .schema import SCHEMA_VERSION, get_questionnaire_schema
   ```

3. ✅ Comprehensive test coverage added (3 focused tests in `backend/questionnaires/tests/test_schema_migration.py`):
   - `test_questionnaire_serialiser_validate_document_accepts_current_schema_version` — Current version accepted
   - `test_questionnaire_serialiser_validate_document_rejects_mismatched_version` — Old version rejected with actionable error message
   - `test_questionnaire_serialiser_validate_document_rejects_edge_cases` — Null, missing, and non-dict inputs rejected

**Important Note**: The API endpoint for questionnaires is currently read-only (`ReadOnlyModelViewSet` with GET/OPTIONS/HEAD only). The validation will be used when write methods (POST/PATCH) are enabled in the future. The validation is already in place and tested for future compatibility.

**Exit criteria** (met):
- ✓ API serializer checks schema_version
- ✓ Error messages guide to migration command
- ✓ 3 focused, non-redundant tests pass
- ✓ All imports at module level per FEATURE-DEVELOPMENT.md
- ✓ Tests organized in dedicated test_schema_migration.py module

---

### Phase 3: Migration File Infrastructure (~4 hours) - PENDING

**Implementation Status**: Not yet started. Will implement after Phase 2 validation is confirmed stable.

**What to do**:

1. Create `backend/questionnaires/schema_migrations_loader.py` with:
   - `get_migration(number: str)` — Import migration module by number
   - `list_migrations() -> list[str]` — List all available migration numbers in order
   - `find_path(from_number, to_number) -> list[str]` — Resolve migration sequence

2. Create `backend/questionnaires/schema_migration_utils.py` with:
   - `validate_transform(doc, from_version, to_version) -> (bool, list[str])` — Validate transform output against schema

3. Create bootstrap migration file `backend/questionnaires/schema_migrations/0001_initial.py`:
   - Establishes `SCHEMA_VERSION = "2025.07-1"` as baseline
   - Identity transforms (forward and backward are no-ops)

**Tests to write**:
- `backend/questionnaires/tests/test_schema_migrations_loader.py` — Test listing, path finding
- Unit tests for `validate_transform()` utility

**Exit criteria**:
- ✓ Migration loader finds and lists migrations
- ✓ Path finding works forward/backward
- ✓ Validation applies transforms correctly and reports errors

---

## Idempotency Design

**Critical requirement**: Running the same migration multiple times must be safe (idempotent).

### Problem

If migration files raise errors on precondition mismatch, you cannot safely retry:

```bash
python manage.py schema_migrate_questionnaire 0001  # First run: ✓ Success
python manage.py schema_migrate_questionnaire 0001  # Second run: ❌ ERROR (precondition failed)
```

This violates idempotency and breaks safe retry semantics.

### Solution: Command-Level Precondition Check

The **management command** (not the migration file) handles idempotency by checking database state before invoking the migration transform:

```python
# backend/questionnaires/management/commands/schema_migrate_questionnaire.py

def get_db_schema_version() -> str | None:
    """Find most common schema_version in database.
    
    Returns:
        - "1" if all/most questionnaires at version 1
        - "2025.07-1" if all/most at old calendar version
        - None if database is empty or mixed (error state)
    """
    from django.db.models import Count
    from questionnaires.models import Questionnaire
    
    versions = (
        Questionnaire.objects
        .values('document__schema_version')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    if not versions:
        return None
    
    return versions[0]['document__schema_version']


class Command(BaseCommand):
    def handle(self, migration_number, dry_run=False, **options):
        # Get current state
        current_db_version = get_db_schema_version()
        migration = get_migration(migration_number)
        target_version = migration.SCHEMA_VERSION
        
        # IDEMPOTENCY CHECK: Already at target?
        if current_db_version == target_version:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Already at version {target_version}. No migration needed."
                )
            )
            return  # Safe no-op; can retry infinitely
        
        # PRECONDITION: Verify DB state matches what migration expects
        # (For migration 0001: expects 2025.07-1; For 0002: expects 1)
        expected_previous = get_expected_previous_version(migration_number)
        
        if current_db_version != expected_previous:
            raise CommandError(
                f"Cannot migrate {migration_number}:\n"
                f"  Current DB version: {current_db_version}\n"
                f"  Expected input: {expected_previous}\n"
                f"  Will produce: {target_version}\n"
                f"  Run 'python manage.py schema_status_questionnaire' to diagnose."
            )
        
        # Run transformation (migration file assumes precondition met)
        self._transform_all_documents(migration, dry_run)
```

### Idempotent Behavior Examples

**Scenario 1: First migration run (transforms data)**
```bash
$ python manage.py schema_status_questionnaire
Current schema version: 2025.07-1
  2025.07-1: 147 questionnaires

$ python manage.py schema_migrate_questionnaire 0001
Found 147 questionnaires at version 2025.07-1
Migrating to version 1...
✓ Migrated 147/147 questionnaires. Updated schema version to 1

$ python manage.py schema_migrate_questionnaire 0001
Already at version 1. No migration needed.
```

**Scenario 2: Running same command twice (safe idempotent retry)**
```bash
$ python manage.py schema_migrate_questionnaire 0002
Already at version 2. No migration needed.
```

**Scenario 3: Mixed database state (error state - cannot migrate)**
```bash
$ python manage.py schema_migrate_questionnaire 0002
Cannot migrate 0002:
  Current DB version: mixed
  Expected input: 1
  Will produce: 2
  Run 'python manage.py schema_status_questionnaire' to diagnose.
```

### Migration File Design (Assumes Precondition Met)

Migration files can assume the management command verified all preconditions:

```python
def migrate_forward(doc: dict) -> dict:
    """Transform version 1 → 2.
    
    The management command verified the precondition before calling this.
    This check is defensive; should never fail in normal operation.
    """
    if doc.get("schema_version") != "1":
        raise ValueError(f"Unexpected version: {doc.get('schema_version')}")
    
    doc = deepcopy(doc)
    doc["schema_version"] = "2"
    return doc
```

**Key point**: Migration files are **simple and focused** because the command layer handles all precondition logic.

---

### Phase 4: Management Commands (~6 hours) - PENDING

**Implementation Status**: Not yet started. Will implement after Phase 3 infrastructure is solid.

**What to do**:

1. Create three command files for questionnaires:
   - `backend/questionnaires/management/commands/schema_migrate_questionnaire.py`
   - `backend/questionnaires/management/commands/schema_rollback_questionnaire.py`
   - `backend/questionnaires/management/commands/schema_status_questionnaire.py`

**Command implementation details**:

- **Arguments**: Migration number only (e.g., `0002`), not version strings. Loader maps number → migration file → reads SCHEMA_VERSION
- **Idempotency**: Command calls `get_db_schema_version()` before running; if already at target version, returns success (no-op, safe to retry)
- **Precondition validation**: Ensures current DB version matches migration's expected input version; fails with clear error if state mismatch
- **Forward migrate**: Applies all forward transforms from current version to target version in a single transaction
- **Backward migrate** (rollback): Applies all backward transforms from current version to target version in a single transaction
- **Status**: Lists current version, shows record distribution by schema_version, lists available migration numbers, detects mixed-version state
- **Dry-run option** (`--dry-run`): Tests transforms without writing; only valid with migrate/rollback, not with status
- **Single transaction**: All records transformed within one database transaction; fail-fast on first error with clear error message showing which record failed
- **Atomic version update**: `SCHEMA_VERSION` constant updated **only after** all transforms succeed and transaction commits (via git commit or code deployment)
- **Helper function** `get_db_schema_version()`: Queries database for most common schema_version across questionnaires; handles mixed-state detection

**Tests to write**:
- `backend/questionnaires/tests/test_schema_migrate_command.py` — Test migrate forward with/without dry-run, idempotency, precondition validation
- `backend/questionnaires/tests/test_schema_rollback_command.py` — Test rollback with/without dry-run, idempotency
- `backend/questionnaires/tests/test_schema_status_command.py` — Test status output, mixed-version detection

**Exit criteria**:
- ✓ All commands parse arguments correctly
- ✓ Idempotent: running same migration twice is safe (second run is no-op)
- ✓ Precondition validation: clear error if DB state mismatches migration expectation
- ✓ Dry-run produces zero database changes
- ✓ Migrate/rollback update version tracking correctly
- ✓ Transaction rollback on any transform error
- ✓ Error messages identify which record failed and why
- ✓ `get_db_schema_version()` helper detects mixed-version state

---

### Phase 5: Fixtures & Test Data (~2 hours) - PENDING

**Implementation Status**: Not yet started. Will implement after Phase 4 commands are working.

**What to do**:

1. Verify existing fixtures in `backend/conftest.py`, `backend/questionnaires/tests/fixtures.py` already use current schema version

2. Create migration test fixtures for old versions (for testing transforms)

**Exit criteria**:
- ✓ Fixtures verified at current version
- ✓ Old-version test fixtures created for command tests

---

### Phase 6: Integration Tests & Documentation (~4 hours) - PENDING

**Implementation Status**: Not yet started. Will implement after all other phases are complete.

**What to do**:

1. Create integration tests:
   - `backend/questionnaires/tests/test_migration_integration.py` — Full lifecycle: create old-version record → migrate → verify

2. Update documentation:
   - **`docs/DEPLOYMENT.md`** — Add "Schema Migrations" section with operator runbook
   - **`docs/BACKEND-CONVENTIONS.md`** — Add "JSON Schema Migrations" section
   - **`docs/TESTING.md`** — Add migration testing patterns

**Exit criteria**:
- ✓ Integration tests pass full lifecycle
- ✓ Operator runbook is clear and actionable
- ✓ Developer guide explains writing future migrations

---

## Applications Module - Future Implementation

The migration framework will be implemented for `Questionnaire.document` first. Once the framework is proven reliable and well-tested in production use, it will be applied to `Application.document` using identical patterns.

**Timeline**: Applications implementation planned after questionnaires framework is stable and any adjustments from real-world use are incorporated.

**Future phases for applications**:
- Phase 1: Add `SCHEMA_VERSION` constant to `backend/applications/schema.py`
- Phase 2: Add schema version validation to `ApplicationSerialiser.validate_document()`
- Phase 3-6: Same as questionnaires (migration infrastructure, commands, fixtures, integration tests)

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

This section demonstrates how the framework will be applied to the first real schema change in questionnaires.

**Status**: Example planned for future implementation. Will demonstrate migration after Phase 4 commands are complete.

### Current State (Schema 1)

Questions have flat extra fields in [backend/questionnaires/serialisers.py](backend/questionnaires/serialisers.py#L98-L135):

```json
{
  "schema_version": "1",
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

### Target State (Schema 2)

Consolidate into single `extra_attributes` object:

```json
{
  "schema_version": "2",
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

### Migration Implementation (Planned)

**Step 1**: Create migration file `backend/questionnaires/schema_migrations/0002_extra_attributes_consolidation.py` (see Architecture section above for full code)

**Step 2**: Update serializer in `backend/questionnaires/serialisers.py`:
- Remove commented-out `QuestionExtraAttrs` (uncomment and activate)
- Remove individual flat fields from `QuestionSerialiser`
- Add `extra_attributes = QuestionExtraAttrs(required=False, allow_null=True, default=None)`

**Step 3**: Update JSON schema in `backend/questionnaires/schema.py` — add `extra_attributes` property to question definition

**Step 4**: Update `SCHEMA_VERSION` constant in `backend/questionnaires/schema.py`:
```python
SCHEMA_VERSION = "2"
```

**Step 5**: Update frontend types in `frontend/src/context/types/Questionnaire.ts`

**Step 6**: Execute migration (after Phase 4 management commands are implemented):
```bash
# Check status
python manage.py schema_status_questionnaire
# Output: Current schema version: 1
#         1: 147 questionnaires

# Dry run
python manage.py schema_migrate_questionnaire 0002 --dry-run
# Output: Found 147 questionnaires at version 1
#         DRY RUN: Would migrate to schema version 2...
#         Would transform 147/147 successfully

# Migrate
python manage.py schema_migrate_questionnaire 0002
# Output: Found 147 questionnaires at version 1
#         Migrating to schema version 2...
#         ✓ Migrated 147/147 questionnaires. Updated version to 2

# Verify
python manage.py schema_status_questionnaire
# Output: Current schema version: 2
#         2: 147 questionnaires
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
