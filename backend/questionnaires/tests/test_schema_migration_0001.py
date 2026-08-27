"""Unit tests for migration 0001: Versioning baseline transition (0 → 1).

Tests specific to the 0001_initial migration file, including:
- Migration transforms (forward and backward)
- Hard-coded schema correctness and immutability
- Transform isolation (only version field changes)
- Idempotency and reversibility guarantees

Migration files are discovered and loaded via the generic schema_migration_framework.
"""

import pytest
from copy import deepcopy
import importlib

from schema_migration_framework.loader import get_migration
from schema_migration_framework.executor import get_migrations_package_path


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


# Ensure the schema_migrations package is importable before getting its path
importlib.import_module("questionnaires.schema_migrations")

# Get the migrations package path once for all tests
_MIGRATIONS_PACKAGE_PATH = get_migrations_package_path("questionnaires.schema_migrations")


@pytest.fixture
def migration_0001():
    """Load migration 0001 via generic framework."""
    return get_migration("0001", _MIGRATIONS_PACKAGE_PATH)


class TestMigration0001Transforms:
    """Test migration 0001 forward/backward transforms (0001_initial.py)."""

    def test_0001_migrate_forward_transforms_version(self, migration_0001):
        """migrate_forward transforms schema_version 0 → 1."""
        doc = {"schema_version": 0, "steps": []}

        result = migration_0001.migrate_forward(doc)

        assert result["schema_version"] == 1
        # Original should not be modified
        assert doc["schema_version"] == 0

    def test_0001_migrate_forward_fails_on_wrong_version(self, migration_0001):
        """migrate_forward raises TypeError if document not at version 0."""
        doc = {"schema_version": 2, "steps": []}

        with pytest.raises(TypeError) as exc_info:
            migration_0001.migrate_forward(doc)

        assert "0" in str(exc_info.value)
        assert "2" in str(exc_info.value)

    def test_0001_migrate_backward_transforms_version(self, migration_0001):
        """migrate_backward transforms schema_version 1 → 0."""
        doc = {"schema_version": 1, "steps": []}

        result = migration_0001.migrate_backward(doc)

        assert result["schema_version"] == 0
        # Original should not be modified
        assert doc["schema_version"] == 1

    def test_0001_migrate_backward_fails_on_wrong_version(self, migration_0001):
        """migrate_backward raises TypeError if document not at version 1."""
        doc = {"schema_version": 0, "steps": []}

        with pytest.raises(TypeError) as exc_info:
            migration_0001.migrate_backward(doc)

        assert "1" in str(exc_info.value)
        assert "0" in str(exc_info.value)


class TestMigration0001PreviousSchemaCorrectness:
    """Verify previous_schema() is hard-coded correctly for version 0 (baseline)."""

    def test_previous_schema_has_correct_version_default(self, migration_0001):
        """previous_schema() must explicitly show it's version 0 (baseline) schema."""
        schema = migration_0001.previous_schema()

        # Must have default set to 0 (integer, not "2025.07-1" string)
        assert schema["properties"]["schema_version"]["default"] == 0
        assert schema["properties"]["schema_version"]["type"] == "integer"

    def test_previous_schema_is_hard_coded_not_imported(self, migration_0001):
        """Verify previous_schema() doesn't call external functions (frozen in time)."""
        # Call it twice - must return identical structure (hard-coded, not dynamic)
        schema1 = migration_0001.previous_schema()
        schema2 = migration_0001.previous_schema()
        
        assert schema1 == schema2
        # Verify it has all expected top-level keys
        assert "$schema" in schema1
        assert "properties" in schema1
        assert "$defs" in schema1
        assert "required" in schema1

    def test_target_schema_has_correct_version_default(self, migration_0001):
        """target_schema() must have default set to 1 (the target version)."""
        schema = migration_0001.target_schema()

        # Must have default set to 1 (target version for this migration)
        assert schema["properties"]["schema_version"]["default"] == 1

    def test_target_schema_is_hard_coded_not_imported(self, migration_0001):
        """Verify target_schema() doesn't call external functions (frozen in time)."""
        # Call it twice - must return identical structure
        schema1 = migration_0001.target_schema()
        schema2 = migration_0001.target_schema()
        
        assert schema1 == schema2
        # Verify it has all expected top-level keys
        assert "$schema" in schema1
        assert "properties" in schema1
        assert "$defs" in schema1
        assert "required" in schema1


class TestMigration0001TransformOnlyVersionChanges:
    """Verify migrations only change schema_version, nothing else."""

    def test_migrate_forward_changes_only_version(self, migration_0001):
        """Forward migration must change ONLY schema_version field."""
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Test",
                    "description": "Desc",
                    "sections": [
                        {
                            "title": "Sec",
                            "description": "SDesc",
                            "questions": [
                                {
                                    "label": "Q",
                                    "type": "text",
                                    "is_required": False,
                                    "description": "QDesc",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        # All fields except schema_version must be identical
        assert result["schema_version"] == 1
        assert result["steps"] == doc["steps"]
        # Verify deep equality of nested structure
        for key in doc:
            if key != "schema_version":
                assert result[key] == doc[key]

    def test_migrate_backward_changes_only_version(self, migration_0001):
        """Backward migration must change ONLY schema_version field."""
        doc = {
            "schema_version": 1,
            "steps": [
                {
                    "title": "Test",
                    "description": "Desc",
                    "sections": [],
                }
            ],
        }
        
        result = migration_0001.migrate_backward(doc)
        
        # All fields except schema_version must be identical
        assert result["schema_version"] == 0
        assert result["steps"] == doc["steps"]


class TestMigration0001Idempotency:
    """Verify transforms are reversible and idempotent."""

    def test_forward_then_backward_equals_identity(self, migration_0001):
        """Apply forward then backward must return to original."""
        doc = {
            "schema_version": 0,
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # Forward: 0 → 1
        forward_result = migration_0001.migrate_forward(deepcopy(doc))
        assert forward_result["schema_version"] == 1
        
        # Backward: 1 → 0
        backward_result = migration_0001.migrate_backward(forward_result)
        
        # Must match original exactly
        assert backward_result == doc

    def test_backward_then_forward_equals_identity(self, migration_0001):
        """Apply backward then forward must return to original."""
        doc = {
            "schema_version": 1,
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # Backward: 1 → 0
        backward_result = migration_0001.migrate_backward(deepcopy(doc))
        assert backward_result["schema_version"] == 0
        
        # Forward: 0 → 1
        forward_result = migration_0001.migrate_forward(backward_result)
        
        # Must match original exactly
        assert forward_result == doc
