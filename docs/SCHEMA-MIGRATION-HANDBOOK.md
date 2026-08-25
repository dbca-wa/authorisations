# Schema Migration Handbook

This handbook provides comprehensive guidance on creating, executing, testing, and rolling back schema migrations for documents in Django models.

**Scope**: This guide is written generically to apply to any Django model with JSON schema versioning. Currently implemented for `Questionnaire.document` only. The framework design is reusable and can be applied to other models (e.g., `Application.document`) following the same patterns documented here.

**Note on library extraction**: The management command names and module paths shown in this handbook are questionnaire-specific (e.g., `schema_migrate_questionnaire`). When this framework is extracted as a standalone library, these commands and paths will be generalized. See cross-references to [SCHEMA-MIGRATION-PLAN.md](SCHEMA-MIGRATION-PLAN.md) and [MIGRATION-FRAMEWORK-LIBRARY-PLAN.md](MIGRATION-FRAMEWORK-LIBRARY-PLAN.md) for strategic planning.

---

## Table of Contents

1. [Overview](#overview)
2. [Creating a New Migration](#creating-a-new-migration)
3. [Writing Migration Code](#writing-migration-code)
4. [Executing a Migration](#executing-a-migration)
5. [Rolling Back a Migration](#rolling-back-a-migration)
6. [Testing Migrations](#testing-migrations)
7. [Troubleshooting](#troubleshooting)
8. [Reference](#reference)

---

## Overview

### What is a Schema Migration?

A schema migration transforms all documents in a database from one schema version to another. When the JSON schema for a document changes (e.g., adding a required field, restructuring nested objects), a migration ensures all existing records conform to the new schema.

**Example**: When moving from schema version "1" to "2", you might:
- Add a new required field with a sensible default
- Rename an existing field
- Consolidate flat fields into a nested object
- Remove deprecated fields

### Why Migrations Matter

- **Safety**: Transforms all data atomically within a transaction; if anything fails, the entire operation rolls back
- **Reversibility**: Each migration includes a backward transform, allowing safe rollback
- **Auditability**: Migration code is stored in git; every schema change is version-controlled
- **Determinism**: Migrations always transform data the same way, regardless of the current schema definition

### Key Concepts

#### 1. Schema Version

An integer identifier representing the structure of a document. Currently:
- **Baseline** (legacy): `0` (integer, deprecated)
- **Ordinal-based** (current): `1`, `2`, `3`, etc. (integers)

The current schema version is stored as a Python constant:
```python
# backend/questionnaires/schema.py
SCHEMA_VERSION = 1
```

All documents in the database must conform to `SCHEMA_VERSION`. The API rejects documents with mismatched versions, directing users to run the migration command.

#### 2. Migration Files

Each migration is a Python module in the `schema_migrations/` directory:

```
backend/questionnaires/schema_migrations/
├── __init__.py
├── 0001_initial.py          # Versioning baseline (version 0 → 1)
├── 0002_consolidate_attrs.py # Future migration (version 1 → 2)
└── 0003_rename_fields.py     # Future migration (version 2 → 3)
```

Each migration file contains four required functions (version derived from filename):
- `previous_schema()` function (hard-coded schema snapshot from previous version)
- `target_schema()` function (hard-coded schema snapshot for this version)
- `migrate_forward(doc)` function (transforms document to new version)
- `migrate_backward(doc)` function (transforms document back to previous version)

**Note**: The schema version is automatically derived from the migration filename (e.g., `0001_initial.py` → version 1). You do NOT need to add a `SCHEMA_VERSION` constant in migration files.

#### 3. Frozen Schemas

**Critical design pattern**: Migration files must define schemas as hard-coded snapshots, never by calling `get_questionnaire_schema()` or looking them up dynamically.

**Why?** Because the current schema will evolve as new migrations are added. If a test tries to validate an old migration against the current schema, the test fails or passes incorrectly.

**Example** (❌ Wrong):
```python
def previous_schema():
    # BAD: This returns the CURRENT schema, not the historical one!
    from questionnaires.schema import get_questionnaire_schema
    return get_questionnaire_schema()
```

**Example** (✅ Correct):
```python
def previous_schema():
    # GOOD: Hard-coded snapshot of what version 1 looked like
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer"},
            "steps": {"type": "array"},
            # ... (rest of schema as it was in version 1)
        }
    }
```

#### 4. Idempotency

**Rule**: Running the same migration command multiple times must be safe (idempotent).

```bash
python manage.py schema_migrate_questionnaire 0002  # First run: transforms data
python manage.py schema_migrate_questionnaire 0002  # Second run: no-op (already at version 2)
```

The management command enforces this by checking the database version before executing any transforms. If already at the target version, it returns immediately with a "no operation needed" message.

---

## Creating a New Migration

### Step 1: Plan the Migration

Before writing code, document what changes:

**Example**: Migration 0002 - Consolidate question attributes

```markdown
**Old schema (version 1)**:
{
  "steps": [
    {
      "sections": [
        {
          "questions": [
            {
              "label": "Name",
              "type": "text",
              "select_options": [...],      // Specific to select questions
              "grid_columns": [...],        // Specific to grid questions
              "dependent_step": "...",       // Specific to conditional questions
            }
          ]
        }
      ]
    }
  ]
}

**New schema (version 2)**:
{
  "steps": [
    {
      "sections": [
        {
          "questions": [
            {
              "label": "Name",
              "type": "text",
              "extra_attributes": {         // Consolidated object
                "select_options": [...],
                "grid_columns": [...],
                "dependent_step": "...",
              }
            }
          ]
        }
      ]
    }
  ]
}

**Rationale**: Reduces schema verbosity. Only questions that have extra attributes include the object.
```

### Step 2: Determine Migration Number

Find the highest existing migration number and add 1:

```bash
# Check existing migrations
ls backend/questionnaires/schema_migrations/
# Output:
# 0001_initial.py
# 0002_consolidate_attrs.py (if it exists)

# Your new migration should be 0003_*.py
```

### Step 3: Create Migration File

Create `backend/questionnaires/schema_migrations/000N_descriptive_name.py`:

```python
"""Migration 0002: Consolidate question attributes (version 1 → 2).

Detailed explanation of what the migration does and why.
Include the business context if relevant.

Version 2 is automatically derived from filename (0002).
"""

from copy import deepcopy


def previous_schema():
    """Return hard-coded schema snapshot from version 1.
    
    Must be frozen (never calls get_questionnaire_schema()).
    This schema definition is preserved forever for migration validation.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "default": 1},
            "steps": {
                "type": "array",
                "items": {"$ref": "#/$defs/step"}
            }
        },
        "$defs": {
            "step": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/section"}
                    }
                }
            },
            "section": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/question"}
                    }
                }
            },
            "question": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "type": {"type": "string"},
                    "select_options": {"type": "array"},  # Old flat fields
                    "grid_columns": {"type": "array"},
                    "dependent_step": {"type": ["string", "null"]}
                }
            }
        }
    }


def target_schema():
    """Return hard-coded schema snapshot for version 2.
    
    Hard-coded like previous_schema(). Represents the new structure.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "default": 2},
            "steps": {
                "type": "array",
                "items": {"$ref": "#/$defs/step"}
            }
        },
        "$defs": {
            "step": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/section"}
                    }
                }
            },
            "section": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/question"}
                    }
                }
            },
            "question": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "type": {"type": "string"},
                    "extra_attributes": {  # New consolidated object
                        "type": "object",
                        "properties": {
                            "select_options": {"type": "array"},
                            "grid_columns": {"type": "array"},
                            "dependent_step": {"type": ["string", "null"]}
                        }
                    }
                }
            }
        }
    }


def migrate_forward(document: dict) -> dict:
    """Transform: version 1 → version 2 (consolidate extra_* → extra_attributes).
    
    Precondition: Called only when document.schema_version == 1.
    The management command verifies this before calling migrate_forward().
    
    If this precondition is violated, raise TypeError with a clear message.
    """
    if document.get("schema_version") != 1:
        raise TypeError(
            f"Expected schema_version 1, got {document.get('schema_version')}"
        )
    
    document = deepcopy(document)
    document["schema_version"] = 2
    
    # Transform each question in each section of each step
    for step in document.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                # Collect all extra_* fields
                extra_attrs = {}
                for field in ["select_options", "grid_columns", "dependent_step"]:
                    if field in question:
                        extra_attrs[field] = question.pop(field)
                
                # Add consolidated object only if there are attributes
                if extra_attrs:
                    question["extra_attributes"] = extra_attrs
    
    return document


def migrate_backward(document: dict) -> dict:
    """Transform: version 2 → version 1 (expand extra_attributes → extra_*).
    
    Rollback support: Restores documents to pre-migration state.
    """
    if document.get("schema_version") != 2:
        raise TypeError(
            f"Expected schema_version 2, got {document.get('schema_version')}"
        )
    
    document = deepcopy(document)
    document["schema_version"] = 1
    
    # Expand consolidated object back to flat fields
    for step in document.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                extra_attrs = question.pop("extra_attributes", {})
                if extra_attrs:
                    question.update(extra_attrs)
    
    return document
```

### Step 4: Update Schema Version Constant

Once your migration is ready, update the version constant in the schema module:

```python
# backend/questionnaires/schema.py
SCHEMA_VERSION = 2  # Updated from 1 to 2
```

Also update the schema definition itself (if the schema is changing):

```python
# backend/questionnaires/schema.py
def get_questionnaire_schema():
    """Return the current schema definition (version 2)."""
    return {
        # ... updated schema structure
    }
```

### Step 5: Create Commit(s)

Commit your migration and schema changes:

```bash
git add backend/questionnaires/schema_migrations/000N_descriptive_name.py
git add backend/questionnaires/schema.py
git commit -m "Migration 000N: Descriptive title

- Consolidate extra_* fields into extra_attributes object
- Update schema version to 2
- Includes forward and backward transforms
"
```

---

## Writing Migration Code

### Transform Function Guidelines

**1. Always deep-copy the document**

```python
# ❌ Wrong: Modifies original dictionary
def migrate_forward(document):
    document["schema_version"] = "2"
    return document

# ✅ Correct: Works on a copy
def migrate_forward(document):
    document = deepcopy(document)
    document["schema_version"] = "2"
    return document
```

**2. Defensive precondition checks**

```python
def migrate_forward(document: dict) -> dict:
    # Verify the precondition before transforming
    if document.get("schema_version") != "1":
        raise ValueError(
            f"Expected schema_version 1, got {document.get('schema_version')}"
        )
    # ... rest of transform
```

**3. Handle edge cases gracefully**

```python
def migrate_forward(document: dict) -> dict:
    document = deepcopy(document)
    
    # Handle missing top-level keys
    for step in document.get("steps", []):  # Default to [] if missing
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                # Transform question...
    
    document["schema_version"] = "2"
    return document
```

**4. Use explicit field movement, not inplace mutation**

```python
# ❌ Less clear
for question in questions:
    question["extra_attributes"] = {k: question.pop(k) for k in extra_fields if k in question}

# ✅ More explicit and easier to debug
for question in questions:
    extra_attrs = {}
    for field in ["select_options", "grid_columns"]:
        if field in question:
            extra_attrs[field] = question.pop(field)
    
    if extra_attrs:
        question["extra_attributes"] = extra_attrs
```

### Testing Your Transform Locally

Before running on the database, test the transform in isolation:

```python
# Interactive Python shell (backend/)
from questionnaires.schema_migrations.0002_consolidate_attrs import migrate_forward, migrate_backward
from questionnaires.tests.factories import questionnaire_factory
from copy import deepcopy

# Create test document at version 1
q = questionnaire_factory(document={"schema_version": 1, "steps": [...]})
old_doc = q.document

# Test forward transform
new_doc = migrate_forward(deepcopy(old_doc))
assert new_doc["schema_version"] == 2
assert new_doc["steps"][0]["sections"][0]["questions"][0].get("extra_attributes") is not None

# Test backward transform
restored_doc = migrate_backward(deepcopy(new_doc))
assert restored_doc == old_doc  # Should be identical

print("✓ Transform works correctly")
```

---

## Executing a Migration

### Pre-Migration Checklist

Before running a migration in production, ensure:

1. ✅ **Code deployed** — New schema.py with updated `SCHEMA_VERSION` is live
2. ✅ **Maintenance mode enabled** — API is serving requests but blocking writes (`MAINTENANCE_MODE=True`)
3. ✅ **Migration tested locally** — Verified transforms work on test data
4. ✅ **Dry-run executed** — Command executed with `--dry-run` to confirm
5. ✅ **Backup available** — Database backup exists (standard practice)

See [DEPLOYMENT.md](DEPLOYMENT.md) for maintenance mode setup.

### Step 1: Check Current Status

```bash
python manage.py schema_status_questionnaire

# Output:
# Current schema version: 1
#   1: 147 questionnaires
# Available migrations: 0001 (you are here), 0002, 0003
```

### Step 2: Dry Run (Test Without Writing)

```bash
python manage.py schema_migrate_questionnaire 0002 --dry-run

# Output:
# Found 147 questionnaires at version 1
# DRY RUN: Would migrate to schema version 2...
# Would transform 147/147 successfully
#
# DRY RUN COMPLETE (no changes made)
```

**What to check**:
- ✓ Counts match your expectation (147 records)
- ✓ All records would transform successfully
- ✓ No errors during transform validation

### Step 3: Execute Migration

```bash
python manage.py schema_migrate_questionnaire 0002

# Output:
# Found 147 questionnaires at version 1
# Migrating to schema version 2...
# ✓ Migrated 147/147 questionnaires. Updated schema version to 2.
#
# MIGRATION COMPLETE
```

### Step 4: Verify Post-Migration

```bash
python manage.py schema_status_questionnaire

# Output:
# Current schema version: 2
#   2: 147 questionnaires
# Available migrations: 0001, 0002 (you are here), 0003
```

**All records must be at version 2.** If you see mixed versions, contact the development team immediately.

### Step 5: Exit Maintenance Mode

Once migration is verified successful, disable maintenance mode in your deployment:

```bash
# Set MAINTENANCE_MODE=False and redeploy, or
# Update your infrastructure configuration to disable maintenance mode
export MAINTENANCE_MODE=False
```

API will now accept POST/PATCH requests using the new schema version.

---

## Rolling Back a Migration

If something goes wrong after a migration, you can safely rollback to the previous version.

**Important**: Rollback must happen in maintenance mode (same as migration). Don't leave the system exposed to writes during rollback.

### Pre-Rollback Checklist

1. ✅ **Maintenance mode enabled** — API is blocking writes
2. ✅ **Identify why rollback is needed** — Document the issue
3. ✅ **Code reverted** (optional) — Code changes can be reverted before rollback, or kept and skipped

### Step 1: Verify Current State

```bash
python manage.py schema_status_questionnaire

# Output should show all records at the version you migrated to
# Current schema version: 2
#   2: 147 questionnaires
```

### Step 2: Dry Run Rollback

```bash
python manage.py schema_rollback_questionnaire 0001

# Output:
# Found 147 questionnaires at version 2
# DRY RUN: Would rollback to schema version 1...
# Would transform 147/147 successfully
#
# DRY RUN COMPLETE (no changes made)
```

### Step 3: Execute Rollback

```bash
python manage.py schema_rollback_questionnaire 0001

# Output:
# Found 147 questionnaires at version 2
# Rolling back to schema version 1...
# ✓ Rolled back 147/147 questionnaires. Updated schema version to 1.
#
# ROLLBACK COMPLETE
```

### Step 4: Verify Rollback

```bash
python manage.py schema_status_questionnaire

# Output:
# Current schema version: 1
#   1: 147 questionnaires
```

**All records must be back at version 1.**

### Step 5: Investigate & Fix

Now that data is rolled back:
1. Fix the issue (update schema definition, migration code, etc.)
2. Test the corrected migration locally
3. Recommit and redeploy
4. Re-run the migration

### Step 6: Exit Maintenance Mode

Once everything is resolved and working:

```bash
export MAINTENANCE_MODE=False
```

---

## Testing Migrations

### Unit Tests: Migration Infrastructure

**File**: `backend/questionnaires/tests/test_schema_migration.py`

Tests the framework components (loader, validator, path finding):

```python
def test_loader_discovers_all_migrations():
    """Verify loader finds all migration files."""
    migrations = schema_migrations_loader.list_migrations()
    assert "0001" in migrations
    assert "0002" in migrations

def test_find_path_forward():
    """Verify path finding works forward."""
    path = schema_migrations_loader.find_path("1", "2")
    assert path == ["0001", "0002"]

def test_find_path_backward():
    """Verify path finding works backward."""
    path = schema_migrations_loader.find_path("2", "1")
    assert path == ["0002", "0001"]

def test_validate_transform_accepts_valid_output():
    """Verify validator accepts valid transforms."""
    doc = {"schema_version": "1", "steps": [...]}
    migration = schema_migrations_loader.get_migration("0002")
    
    transformed = migration.migrate_forward(deepcopy(doc))
    is_valid, errors = validate_transform(
        transformed,
        "1",
        "2",
        migration.previous_schema(),
        migration.target_schema()
    )
    
    assert is_valid
    assert not errors
```

### Unit Tests: Migration-Specific

**File**: `backend/questionnaires/tests/test_schema_migration_000N.py` (where N is the migration number)

Tests a specific migration's transform logic:

```python
# backend/questionnaires/tests/test_schema_migration_0002.py

import pytest
from copy import deepcopy
from questionnaires.schema_migrations.schema_migrations_loader import get_migration


@pytest.mark.django_db
class TestSchemaMigration0002:
    """Test migration 0002: Consolidate question attributes."""
    
    @pytest.fixture
    def migration(self):
        return get_migration("0002")
    
    def test_migrate_forward_consolidates_select_options(self, migration):
        """Verify select_options → extra_attributes.select_options."""
        doc = {
            "schema_version": "1",
            "steps": [
                {
                    "sections": [
                        {
                            "questions": [
                                {
                                    "label": "Choose one",
                                    "type": "select",
                                    "select_options": ["A", "B", "C"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = migration.migrate_forward(deepcopy(doc))
        
        assert result["schema_version"] == "2"
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "select_options" not in question
        assert question["extra_attributes"]["select_options"] == ["A", "B", "C"]
    
    def test_migrate_forward_handles_missing_extra_fields(self, migration):
        """Verify transform handles questions without extra attributes."""
        doc = {
            "schema_version": "1",
            "steps": [
                {
                    "sections": [
                        {
                            "questions": [
                                {
                                    "label": "Name",
                                    "type": "text"
                                    # No select_options, grid_columns, etc.
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = migration.migrate_forward(deepcopy(doc))
        
        assert result["schema_version"] == "2"
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "extra_attributes" not in question  # No object added if empty
    
    def test_migrate_backward_expands_extra_attributes(self, migration):
        """Verify backward transform expands extra_attributes."""
        doc = {
            "schema_version": "2",
            "steps": [
                {
                    "sections": [
                        {
                            "questions": [
                                {
                                    "label": "Choose one",
                                    "type": "select",
                                    "extra_attributes": {
                                        "select_options": ["A", "B", "C"]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = migration.migrate_backward(deepcopy(doc))
        
        assert result["schema_version"] == "1"
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "extra_attributes" not in question
        assert question["select_options"] == ["A", "B", "C"]
    
    def test_forward_then_backward_is_identity(self, migration):
        """Verify forward + backward = original document."""
        original = {
            "schema_version": "1",
            "steps": [
                {
                    "sections": [
                        {
                            "questions": [
                                {
                                    "label": "Choose",
                                    "type": "select",
                                    "select_options": ["A", "B"],
                                    "grid_columns": ["Col1", "Col2"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        forward = migration.migrate_forward(deepcopy(original))
        backward = migration.migrate_backward(deepcopy(forward))
        
        assert backward == original
    
    def test_previous_schema_is_frozen(self, migration):
        """Verify previous_schema returns hard-coded snapshot (not dynamic)."""
        schema = migration.previous_schema()
        # Should have version "1" properties, not "2"
        assert schema["properties"]["schema_version"]["default"] == "1"
    
    def test_target_schema_is_frozen(self, migration):
        """Verify target_schema returns hard-coded snapshot."""
        schema = migration.target_schema()
        # Should have version "2" properties, not "1"
        assert schema["properties"]["schema_version"]["default"] == "2"
```

### Integration Tests: Full Workflow

**File**: `backend/questionnaires/tests/test_schema_migration_integration.py` (Future: Phase 6)

**TODO**: When implementing Phase 6, add integration test for multi-step migration chain:

```python
# TODO: test_multi_step_migration_chain_baseline_to_version_1
# 
# Test: Create questionnaire at version 0 (baseline) → migrate to 0001 → verify version 1
# Verify: Final document conforms to version 1 schema with all fields intact
# Purpose: Validate that migration execution works end-to-end with realistic data
```

Full integration tests validate the complete workflow:

```python
# backend/questionnaires/tests/test_schema_migration_integration.py

@pytest.mark.django_db
def test_full_migration_lifecycle_with_realistic_questionnaire():
    """End-to-end: create at old version → migrate → verify.
    
    This is an integration test (not unit test) because it:
    - Uses real database records (not mocks)
    - Tests multiple components together (loader, validator, command)
    - Exercises the full CLI workflow
    """
    # Create realistic questionnaire with many questions/sections at version 1
    q = questionnaire_factory(
        document={
            "schema_version": "1",
            "steps": [
                {
                    "title": "Application Step",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": f"Question {i}",
                                    "type": "text",
                                    "select_options": ["A", "B", "C"] if i % 2 == 0 else None,
                                }
                                for i in range(10)
                            ]
                        }
                        for _ in range(3)
                    ]
                }
            ]
        }
    )
    
    # Run migrate command
    call_command("schema_migrate_questionnaire", "0002")
    
    # Verify
    q.refresh_from_db()
    assert q.document["schema_version"] == "2"
    
    # Verify structure is preserved
    assert len(q.document["steps"]) == 1
    assert len(q.document["steps"][0]["sections"]) == 3
    assert len(q.document["steps"][0]["sections"][0]["questions"]) == 10
    
    # Verify transformations applied correctly
    for i, question in enumerate(q.document["steps"][0]["sections"][0]["questions"]):
        if i % 2 == 0:
            assert "extra_attributes" in question
            assert question["extra_attributes"]["select_options"] == ["A", "B", "C"]
        else:
            assert "extra_attributes" not in question
```

### Running Tests

```bash
# All migration tests
cd backend && poetry run pytest questionnaires/tests/test_schema_migration*.py -v

# Specific migration
cd backend && poetry run pytest questionnaires/tests/test_schema_migration_0002.py -v

# With coverage
cd backend && poetry run pytest questionnaires/tests/test_schema_migration*.py --cov=questionnaires --cov-report=term-missing
```

---

## Troubleshooting

### Issue: "Cannot migrate 0002: Current DB version: mixed"

**Cause**: Database contains records at multiple schema versions (indicates a failed/partial migration).

**Resolution**:
1. Check status to identify the problematic records:
   ```bash
   python manage.py schema_status_questionnaire
   # Output shows distribution by version
   ```
2. Investigate why records are at different versions
3. Usually caused by a failed migration that didn't complete atomically
4. Options:
   - Restore from database backup and re-run migration
   - Or manually update the mismatched records (requires database access)
   - Contact development team for assistance

### Issue: "Migration command times out on large dataset"

**Cause**: Millions of records take time to transform; timeout is too short.

**Resolution**:
1. Increase timeout in your command execution:
   ```bash
   # Example: 5-minute timeout
   timeout 300 python manage.py schema_migrate_questionnaire 0002
   ```
2. Or run in background with nohup:
   ```bash
   nohup python manage.py schema_migrate_questionnaire 0002 > migration.log 2>&1 &
   ```
3. Monitor the log to ensure completion:
   ```bash
   tail -f migration.log
   ```

### Issue: "Transform validation failed: document doesn't match schema"

**Cause**: Migration transform produces invalid output (doesn't conform to target schema).

**Resolution**:
1. Check if the migration code has a bug:
   - Review migrate_forward() logic
   - Test locally with sample documents
   - Add debug logging to see transformed output
2. Fix the bug in migration file
3. Re-run the migration (idempotent; safe to retry)

### Issue: "Rollback failed: Expected schema_version 2, got 1"

**Cause**: Trying to rollback from a version different than what rollback expects.

**Resolution**:
1. Check current state:
   ```bash
   python manage.py schema_status_questionnaire
   ```
2. Verify you're rolling back from the correct version:
   ```bash
   # If currently at version 2, roll back to version 1
   python manage.py schema_rollback_questionnaire 0001
   ```

---

## Reference

### Directory Structure

```
backend/
├── questionnaires/
│   ├── schema.py — Current schema definition and SCHEMA_VERSION constant
│   ├── schema_migrations_loader.py — Loader, path finder, migration discovery
│   ├── schema_migration_utils.py — Validation utility
│   ├── schema_migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py — Baseline migration
│   │   ├── 0002_consolidate_attrs.py — Future migration
│   │   └── ...
│   ├── management/commands/
│   │   ├── schema_migrate_questionnaire.py — Execute forward migration
│   │   ├── schema_rollback_questionnaire.py — Execute rollback
│   │   └── schema_status_questionnaire.py — Display status
│   └── tests/
│       ├── test_schema_migration.py — Framework tests
│       ├── test_schema_migration_0001.py — Migration 0001 tests
│       ├── test_schema_migration_000N.py — Migration N tests
│       └── test_schema_migration_integration.py — Integration tests (future)
```

### Command Reference

| Command | Purpose | Syntax |
|---------|---------|--------|
| `schema_status_questionnaire` | Show current version and record distribution | `python manage.py schema_status_questionnaire` |
| `schema_migrate_questionnaire` | Migrate to target version | `python manage.py schema_migrate_questionnaire 0002 [--dry-run]` |
| `schema_rollback_questionnaire` | Rollback to target version | `python manage.py schema_rollback_questionnaire 0001 [--dry-run]` |

### Key Files

| File | Purpose |
|------|---------|
| [SCHEMA-MIGRATION-PLAN.md](SCHEMA-MIGRATION-PLAN.md) | Strategic overview of migration framework design and phases |
| [BACKEND-CONVENTIONS.md](BACKEND-CONVENTIONS.md) | Django API conventions (related: JSON schema patterns) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment procedures (related: maintenance mode setup) |
| [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md) | Feature development checklist (includes test requirements) |

### External Resources

- [JSON Schema Specification](https://json-schema.org/) — Schema syntax and validation rules
- [Django Migrations](https://docs.djangoproject.com/en/5.0/topics/migrations/) — Django's migration philosophy (this framework is inspired by it)
- [jsonschema Library](https://python-jsonschema.readthedocs.io/) — Python JSON schema validation

---

## Questions?

- **Implementation questions**: See [SCHEMA-MIGRATION-PLAN.md](SCHEMA-MIGRATION-PLAN.md) for design decisions
- **Framework extraction strategy**: See [MIGRATION-FRAMEWORK-LIBRARY-PLAN.md](MIGRATION-FRAMEWORK-LIBRARY-PLAN.md)
- **Deployment-specific questions**: See [DEPLOYMENT.md](DEPLOYMENT.md) and related infrastructure docs
