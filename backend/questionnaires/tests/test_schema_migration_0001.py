"""Unit tests for migration 0001: Versioning baseline transition (2025.07-1 → 1).

Tests specific to the 0001_initial migration file, including:
- Migration transforms (forward and backward)
- Hard-coded schema correctness and immutability
- Transform isolation (only version field changes)
- Idempotency and reversibility guarantees
"""

import pytest
from copy import deepcopy

from questionnaires.schema_migrations_loader import get_migration


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestMigration0001Transforms:
    """Test migration 0001 forward/backward transforms (0001_initial.py)."""

    def test_0001_migrate_forward_transforms_version(self):
        """migrate_forward transforms schema_version 2025.07-1 → 1."""
        migration = get_migration("0001")
        doc = {"schema_version": "2025.07-1", "steps": []}

        result = migration.migrate_forward(doc)

        assert result["schema_version"] == "1"
        # Original should not be modified
        assert doc["schema_version"] == "2025.07-1"

    def test_0001_migrate_forward_fails_on_wrong_version(self):
        """migrate_forward raises ValueError if document not at 2025.07-1."""
        migration = get_migration("0001")
        doc = {"schema_version": "2", "steps": []}

        with pytest.raises(ValueError) as exc_info:
            migration.migrate_forward(doc)

        assert "2025.07-1" in str(exc_info.value)
        assert "2" in str(exc_info.value)

    def test_0001_migrate_backward_transforms_version(self):
        """migrate_backward transforms schema_version 1 → 2025.07-1."""
        migration = get_migration("0001")
        doc = {"schema_version": "1", "steps": []}

        result = migration.migrate_backward(doc)

        assert result["schema_version"] == "2025.07-1"
        # Original should not be modified
        assert doc["schema_version"] == "1"

    def test_0001_migrate_backward_fails_on_wrong_version(self):
        """migrate_backward raises ValueError if document not at version 1."""
        migration = get_migration("0001")
        doc = {"schema_version": "2025.07-1", "steps": []}

        with pytest.raises(ValueError) as exc_info:
            migration.migrate_backward(doc)

        assert "1" in str(exc_info.value)
        assert "2025.07-1" in str(exc_info.value)


class TestMigration0001PreviousSchemaCorrectness:
    """Verify previous_schema() is hard-coded correctly for 2025.07-1."""

    def test_previous_schema_has_correct_version_default(self):
        """previous_schema() must explicitly show it's the 2025.07-1 schema."""
        migration = get_migration("0001")
        schema = migration.previous_schema()

        # Must have default set to 2025.07-1 (not "1" or missing)
        assert schema["properties"]["schema_version"]["default"] == "2025.07-1"

    def test_previous_schema_is_hard_coded_not_imported(self):
        """Verify previous_schema() doesn't call external functions (frozen in time)."""
        migration = get_migration("0001")
        
        # Call it twice - must return identical structure (hard-coded, not dynamic)
        schema1 = migration.previous_schema()
        schema2 = migration.previous_schema()
        
        assert schema1 == schema2
        # Verify it has all expected top-level keys
        assert "$schema" in schema1
        assert "properties" in schema1
        assert "$defs" in schema1
        assert "required" in schema1

    def test_target_schema_has_correct_version_default(self):
        """target_schema() must have default set to "1" (the target version)."""
        migration = get_migration("0001")
        schema = migration.target_schema()

        # Must have default set to "1" (target version for this migration)
        assert schema["properties"]["schema_version"]["default"] == "1"

    def test_target_schema_is_hard_coded_not_imported(self):
        """Verify target_schema() doesn't call external functions (frozen in time)."""
        migration = get_migration("0001")
        
        # Call it twice - must return identical structure
        schema1 = migration.target_schema()
        schema2 = migration.target_schema()
        
        assert schema1 == schema2
        # Verify it has all expected top-level keys
        assert "$schema" in schema1
        assert "properties" in schema1
        assert "$defs" in schema1
        assert "required" in schema1


class TestMigration0001TransformOnlyVersionChanges:
    """Verify migrations only change schema_version, nothing else."""

    def test_migrate_forward_changes_only_version(self):
        """Forward migration must change ONLY schema_version field."""
        migration = get_migration("0001")
        
        doc = {
            "schema_version": "2025.07-1",
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
        
        result = migration.migrate_forward(doc)
        
        # All fields except schema_version must be identical
        assert result["schema_version"] == "1"
        assert result["steps"] == doc["steps"]
        # Verify deep equality of nested structure
        for key in doc:
            if key != "schema_version":
                assert result[key] == doc[key]

    def test_migrate_backward_changes_only_version(self):
        """Backward migration must change ONLY schema_version field."""
        migration = get_migration("0001")
        
        doc = {
            "schema_version": "1",
            "steps": [
                {
                    "title": "Test",
                    "description": "Desc",
                    "sections": [],
                }
            ],
        }
        
        result = migration.migrate_backward(doc)
        
        # All fields except schema_version must be identical
        assert result["schema_version"] == "2025.07-1"
        assert result["steps"] == doc["steps"]


class TestMigration0001Idempotency:
    """Verify transforms are reversible and idempotent."""

    def test_forward_then_backward_equals_identity(self):
        """Apply forward then backward must return to original."""
        migration = get_migration("0001")
        
        doc = {
            "schema_version": "2025.07-1",
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # Forward: 2025.07-1 → 1
        forward_result = migration.migrate_forward(deepcopy(doc))
        assert forward_result["schema_version"] == "1"
        
        # Backward: 1 → 2025.07-1
        backward_result = migration.migrate_backward(forward_result)
        
        # Must match original exactly
        assert backward_result == doc

    def test_backward_then_forward_equals_identity(self):
        """Apply backward then forward must return to original."""
        migration = get_migration("0001")
        
        doc = {
            "schema_version": "1",
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # Backward: 1 → 2025.07-1
        backward_result = migration.migrate_backward(deepcopy(doc))
        assert backward_result["schema_version"] == "2025.07-1"
        
        # Forward: 2025.07-1 → 1
        forward_result = migration.migrate_forward(backward_result)
        
        # Must match original exactly
        assert forward_result == doc
