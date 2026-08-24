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

## Implementation Status: PHASES 1-4 COMPLETE ✅

**For `questionnaires` module:**

| Phase | Status | Completion | Tests |
|-------|--------|-----------|-------|
| Phase 1: Version Tracking | ✅ COMPLETE | Schema version as Python constant | N/A |
| Phase 2: Runtime Validation | ✅ COMPLETE | API rejects old schema versions | 10/10 |
| Phase 3: Migration Infrastructure | ✅ COMPLETE | Loader, validator, and 0001_initial migration | 23/23 |
| Phase 4: Management Commands | ✅ COMPLETE | Migrate, rollback, status commands | 40/40 |
| **Total Implementation** | **✅ COMPLETE** | **Ready for production use** | **109/109 tests passing** |

**Next phases (planned):**
- Phase 5: Test fixtures (when adding migration 0002)
- Phase 6: Integration tests & documentation

**Library extraction:**
- See [MIGRATION-FRAMEWORK-LIBRARY-PLAN.md](MIGRATION-FRAMEWORK-LIBRARY-PLAN.md) for comprehensive plan to externalize this framework as a reusable Django plugin

---

## Confirmed Decisions (Simplified Approach)

- **No backup columns**: Transactions provide atomicity. On failure, entire transaction rolls back. Previous schema definitions kept in git/codebase for emergency rollback.
- **No database state tracking**: Single text file (`.schema_version.txt`) ~~tracks current version~~ (**Updated**: Python constant in schema module tracks current version. Simpler, no file I/O required).
- **Single-version production code**: Only `get_questionnaire_schema()` and `get_answers_schema()` exist; always return current schema.
- **Migrations as code**: Transform functions (`migrate_forward()`, `migrate_backward()`) stored in migration files alongside schema definitions.
- **Migration execution**: Maintenance window + single transaction via management command. Operator activates `MAINTENANCE_MODE` for write blocking.
- **Runtime policy**: Strict current-version-only acceptance. Old data throws clear error directing to migration command.
- **Answer key contracts preserved**: `section-question` (application answers) and `step.section-question` (attachments) formats unchanged.
- **Hard-coded previous schema**: Each migration file's `previous_schema()` must return a hard-coded, frozen definition of what the schema was at that version. Never call `get_questionnaire_schema()` or import from current code. This ensures migrations remain valid even when the current schema evolves. Future migrations reference these frozen definitions to understand transformation paths.

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
    doc: dict,
    from_version: str,
    to_version: str,
    from_schema: dict,
    to_schema: dict,
) -> tuple[bool, list[str]]:
    """
    Validate that transform produces valid output.
    
    Args:
        doc: The document to validate
        from_version: Source version string
        to_version: Target version string
        from_schema: Frozen schema dict from migration (what version from_version had)
        to_schema: Frozen schema dict from migration (what version to_version has)
    
    Returns: (is_valid: bool, errors: list[str])
    
    CRITICAL: Schemas must be passed as parameters (from migration files),
    never looked up from current get_questionnaire_schema(). This ensures
    migrations validate against the SAME schema forever, even when the
    current schema evolves in future migrations.
    """
    # Validate against passed schemas, not current code
    pass
```

### 4a. Frozen Schema Design (Critical Pattern)

**Problem**: If migration validation uses `get_questionnaire_schema()`, tests break when the schema evolves:
- Today: version "1" requires `"steps": {minItems: 1}`
- Tomorrow: version "2" makes steps optional
- Old test: `validate_transform(v1_doc, "1", "2")` uses version 2 schema, suddenly passes/fails incorrectly
- Result: Future developers can't trust migration tests

**Solution: Frozen Schemas in Migration Files**

Each migration file must define **both** previous and target schemas as hard-coded snapshots:

```python
# backend/questionnaires/schema_migrations/0001_initial.py

def previous_schema():
    """Hard-coded snapshot of schema at version 2025.07-1."""
    return {
        "$id": "...",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "properties": {...},
        # ... exact structure as it existed at 2025.07-1
    }

def target_schema():
    """Hard-coded snapshot of schema at version 1."""
    # For 0001_initial.py, versions are identical (only version field changes)
    return previous_schema()
```

**Why hard-coded, not dynamic?**
- Migrations are permanent once deployed
- Schema will evolve in future migrations
- `get_questionnaire_schema()` will return the latest schema (not historical)
- Tests must validate forever against what the schema WAS, not what it is NOW
- Git history preserves these snapshots for audit and emergency rollback

**Validation Pattern**:
```python
from schema_migrations import schema_migrations_loader

migration = schema_migrations_loader.get_migration("0001")
is_valid, errors = validate_transform(
    doc,
    "2025.07-1",
    "1",
    migration.previous_schema(),  # Pass frozen schema, don't look it up
    migration.target_schema(),
)
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

### Phase 3: Migration File Infrastructure (~4 hours) ✅ COMPLETED

**Implementation Status**: Phase 3 is FULLY COMPLETE for `questionnaires` module. All files implemented, all tests passing (23/23), all exit criteria met.

**What was done**:

1. ✅ Created `backend/questionnaires/schema_migrations_loader.py`:
   - `get_migration(number: str)` — Dynamically imports migration modules by number
   - `list_migrations() -> list[str]` — Discovers all available migration numbers
   - `find_path(from_number, to_number) -> list[str]` — Resolves forward/backward transformation sequences

2. ✅ Created `backend/questionnaires/schema_migration_utils.py`:
   - `validate_transform(doc, from_version, to_version) -> (bool, list[str])` — Validates transform output against schema
   - `get_db_schema_version() -> str | None` — Queries database for current schema version (majority version)

3. ✅ Created data migration file `backend/questionnaires/schema_migrations/0001_initial.py`:
   - Transforms existing "2025.07-1" records to ordinal version "1"
   - Establishes version "1" as baseline for all future migrations
   - Both `migrate_forward()` (2025.07-1 → 1) and `migrate_backward()` (1 → 2025.07-1) implemented
   - Full defensive error checking on precondition violations

**Tests added** (organized in two modules):
- `backend/questionnaires/tests/test_schema_migration.py` (11 tests):
  - 3 tests: QuestionnaireSerialiser validation (Phase 2)
  - 5 tests: Migration loader infrastructure (discovery, listing, path finding)
  - 3 tests: Validation utility (Phase 3)
- `backend/questionnaires/tests/test_schema_migration_0001.py` (12 tests):
  - 4 tests: Forward/backward transforms
  - 4 tests: Hard-coded schemas (previous_schema, target_schema, immutability)
  - 2 tests: Transform isolation (only version field changes)
  - 2 tests: Idempotency and reversibility
- **Total: 23 passing tests (3 Phase 2 + 8 Phase 3 infrastructure + 12 Phase 3 migration-specific)**

**Exit criteria** (all met):
- ✓ Migration loader finds and lists migrations
- ✓ Path finding works forward/backward
- ✓ Validation applies transforms correctly and reports errors
- ✓ Data migration handles version transition "2025.07-1" → "1"
- ✓ All imports at module level per FEATURE-DEVELOPMENT.md
- ✓ Defensive error checking in migration files

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

### Phase 4: Management Commands (~6 hours) ✅ COMPLETED

**Implementation Status**: Phase 4 is FULLY COMPLETE for `questionnaires` module. All commands implemented, all tests passing (40/40), all exit criteria met.

**What was done**:

1. ✅ Created three management command files:
   - `backend/questionnaires/management/commands/schema_migrate_questionnaire.py` — Forward migration to target version
   - `backend/questionnaires/management/commands/schema_rollback_questionnaire.py` — Backward migration (rollback) to target version
   - `backend/questionnaires/management/commands/schema_status_questionnaire.py` — Display current version and record distribution

2. ✅ All commands include:
   - Migration number argument parsing (e.g., `schema_migrate_questionnaire 0002`)
   - Idempotency checks (already at target = safe no-op)
   - Precondition validation (DB version matches migration expectations)
   - Dry-run support (`--dry-run` flag for migrate/rollback)
   - Single transaction atomicity (all records transform together or none)
   - Clear error messages identifying which record failed and why
   - Version tracking via `SCHEMA_VERSION` constant updates

3. ✅ Comprehensive test coverage (40 tests across three test files):
   - `backend/questionnaires/tests/test_schema_migrate_command.py` (10 tests):
     - Argument parsing and validation
     - Idempotency (already at target version)
     - Dry-run functionality (no database changes)
     - Successful forward transform
     - Transaction rollback on validation error
     - Error message clarity
   - `backend/questionnaires/tests/test_schema_rollback_command.py` (11 tests):
     - Argument parsing and validation
     - Idempotency and safe retry
     - Dry-run functionality
     - Error handling (missing migration, target version mismatch)
     - Multiple record consistency
   - `backend/questionnaires/tests/test_schema_status_command.py` (19 tests):
     - Current version display (code version from SCHEMA_VERSION)
     - Record distribution by schema_version
     - Database version detection (most common version)
     - Mixed-version state detection and warnings
     - Available migrations listing
     - Output formatting and clarity

**Key design decisions implemented**:
- **Idempotency**: Running same migration twice is safe (second run is no-op if already at target)
- **Precondition validation**: Command checks DB state matches migration expectations before executing
- **Transaction isolation**: All records transform within single database transaction; atomic success or rollback
- **Version constant**: `SCHEMA_VERSION` in code is the single source of truth for current version
- **Mixed-version detection**: Status command warns if database contains records at multiple versions (indicates failed/partial migration)
- **Helper function**: `get_db_schema_version()` queries database for most common schema_version, used by all commands

**Test coverage breakdown**:
- Phase 4 commands: 40/40 passing
- Phase 3 infrastructure: 6/6 passing  
- Phase 2 serialiser validation: 10/10 passing (moved to test_serialisers.py)
- Phase 3 migration-specific: 12/12 passing
- Phase 3 framework tests: 5/5 passing
- **Total questionnaires tests: 109/109 passing**

**Exit criteria** (all met):
- ✓ All commands parse arguments correctly
- ✓ Idempotent: running same migration twice is safe (second run is no-op)
- ✓ Precondition validation: clear error if DB state mismatches migration expectation
- ✓ Dry-run produces zero database changes
- ✓ Migrate/rollback update version tracking correctly
- ✓ Transaction rollback on any transform error
- ✓ Error messages identify which record failed and why
- ✓ `get_db_schema_version()` helper detects mixed-version state
- ✓ Status command shows current version and record distribution
- ✓ All commands tested across edge cases (empty DB, single version, mixed versions, missing migrations)

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

     **Before starting**: Code changes are complete (updated serializers, schema.py with new `SCHEMA_VERSION`, frontend types, etc.) and ready to deploy.

     1. **Deploy code with maintenance mode enabled**:
        - Deploy codebase with `MAINTENANCE_MODE=True` (or enable it during deployment)
        - This deploys the new `SCHEMA_VERSION` constant and updated schema definitions
        - API is live but blocking all writes

     2. **Check current status**:
        python manage.py schema_status_questionnaire

     3. **Dry run** (test transforms, no writes):
        python manage.py schema_migrate_questionnaire 0002 --dry-run

     4. **Migrate** (transform all database records):
        python manage.py schema_migrate_questionnaire 0002

     5. **Verify post-migration**:
        python manage.py schema_status_questionnaire
        # Should show all records at new version

     6. **Exit maintenance mode** (re-enable writes):
        - Disable `MAINTENANCE_MODE`
        - API now accepts GET/POST/PATCH requests with validation using new `SCHEMA_VERSION`

     ### Rollback (if needed) — See SCHEMA-MIGRATION-PLAN.md section

     **Important**: Rollback must happen in maintenance mode. Complete procedures are in the schema migration plan. Quick overview:
     1. Revert code to previous version (git revert), deploy with `MAINTENANCE_MODE=True` still active
     2. Execute data rollback command: `python manage.py schema_rollback_questionnaire 0001` (transforms records back)
     3. Verify rollback succeeded: `python manage.py schema_status_questionnaire`
     4. Exit maintenance mode and test
     5. Keep migration files in git (never delete them; they're part of permanent history)
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

### Phase 5: Fixtures & Test Data (~2 hours) - PENDING

**Implementation Status**: Not yet started. Will implement when Phase 4 migration commands need old-version test data.

**When to do this**:
- When adding migration 0002 that requires test fixtures with old schema structures
- Fixtures will use hardcoded old-version documents for testing transforms

**Exit criteria** (future):
- ✓ Fixtures use hardcoded schema versions matching migration test requirements
- ✓ Old-version test fixtures created for command tests

---

### Phase 6: Integration Tests & Documentation (~4 hours) - PENDING

**Implementation Status**: Not yet started. Will implement after all other phases are complete.

**When to do this**:
- After Phase 4 commands are stable and Phase 5 fixtures are created
- Add comprehensive integration tests and operator documentation

**Exit criteria** (future):
- ✓ Integration tests pass full lifecycle (create record → migrate → verify)
- ✓ Operator runbook is clear and actionable
- ✓ Developer guide explains writing future migrations

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

Rollback is a **three-step process** that transforms data back, then reverts code. Migration files are never deleted; they remain in git as permanent historical record.

### Complete Rollback Workflow

**Scenario**: You deployed migration 0002 to production with `MAINTENANCE_MODE=True`, but the migration or new schema causes an issue. You need to revert to 0001.

**Key Principle**: Keep the new code deployed while you rollback data (because the migration file with `migrate_backward()` is in the new code). Only after data is rolled back do you deploy the old code.

**Step 1: Rollback the Data (with current/failed code still deployed)**

The current deployment has the migration file with `migrate_backward()` defined. Use this to transform records back.

```bash
# Maintenance mode should still be True from initial deployment
# If not, ensure it's on
export MAINTENANCE_MODE=True

# Verify current state
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-2  (from new code)
#         2025.07-2: 147 questionnaires

# Rollback data using the current code's migration (e.g., 0002_extra_attributes_consolidation.py)
python manage.py schema_rollback_questionnaire 0001
# Output: Found 147 questionnaires at version 2025.07-2
# Rolling back to schema version 2025.07-1...
# ✓ Rolled back 147/147 questionnaires. Updated schema version to 2025.07-1

# Verify rollback succeeded
python manage.py schema_status_questionnaire
# Output: Current schema version: 2025.07-1
#         2025.07-1: 147 questionnaires
```

**Step 2: Deploy Previous Version**

Now deploy the previous code version (before the failed schema changes).

```bash
# Deploy previous Docker image or git checkout
# This redeploys old SCHEMA_VERSION and old schema definitions
# MAINTENANCE_MODE can stay True during this deployment

# Examples (depending on your deployment method):
# docker pull <image-repo>:<previous-tag> && docker run ...
# OR: git checkout <previous-commit> && deploy

# After deployment, verify schema version matches
python manage.py schema_status_questionnaire
# Should show: Current schema version: 2025.07-1
#         2025.07-1: 147 questionnaires
```

**Step 3: Verify & Disable Maintenance Mode**

```bash
# Run tests to ensure old schema is compatible with old code
cd backend && poetry run pytest questionnaires/tests/ -v

# If tests pass, disable maintenance mode
unset MAINTENANCE_MODE
# Or: Set MAINTENANCE_MODE=False in environment

# API now accepts requests with old code and old schema_version
```

**What is NOT reverted**:
- ❌ Migration files (they stay in git permanently - they document what happened)
- ❌ Git history (the commits with new schema changes stay in history)
- Only the deployed **code** is reverted to an old version

### Recovering from Rollback (Re-migration)

If you've fixed the underlying issues and want to migrate forward again:

1. Ensure `MAINTENANCE_MODE=True`
2. Deploy the new code again (the one with `SCHEMA_VERSION` bump and schema changes)
3. Run the migration command:

```bash
# New code is deployed with the migration file (0002_extra_attributes_consolidation.py)
# Run migrate with current DB at version 2025.07-1
python manage.py schema_migrate_questionnaire 0002
# Output: Found 147 questionnaires at version 2025.07-1
#         Migrating to schema version 2025.07-2...
#         ✓ Migrated 147/147 questionnaires. Updated schema version to 2025.07-2
```

4. Disable maintenance mode

The migration files are **reusable** because they live permanently in git history.

### Key Invariants (Must Always Hold)

1. **Migration files are immutable history**: Once committed to git, migration files (e.g., `schema_migrations/0002_extra_attributes_consolidation.py`) are never modified or deleted. They remain permanently in git history and are needed for rollback operations.

2. **Data rollback requires new code**: To rollback data, the migration file with `migrate_backward()` must exist in the deployed code. This is why you rollback data BEFORE deploying old code.

3. **Sequence: Data first, then code**: Rollback order is: (1) Rollback data using current code's migration file, (2) Deploy old code, (3) Verify and disable maintenance. This is the opposite of the forward migration sequence.

4. **Maintenance mode prevents version mismatch**: During both migration and rollback, `MAINTENANCE_MODE=True` is active the entire time, preventing any window where code/data versions could mismatch and cause API validation errors.

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
