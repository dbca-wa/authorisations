"""Unit tests for migration 0000: Questionnaires calendar-to-ordinal bridge.

Tests the 0000_initial migration, which:
- Serves as forward-only bridge from calendar ("2025.07-1") to ordinal (v0) versioning
- Maps calendar versions to v0
- Ensures documents at v0 remain at v0 (identity when already migrated)
- Does NOT support backward migration (bridge is one-way)

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
def migration_0000():
    """Load migration 0000 via generic framework."""
    return get_migration("0000", _MIGRATIONS_PACKAGE_PATH)


class TestMigration0000ForwardTransform:
    """Test migration 0000 forward transform (forward-only bridge)."""

    def test_0000_migrate_forward_bridges_calendar_to_version_0(self, migration_0000):
        """migrate_forward bridges calendar version "2025.07-1" to v0."""
        doc = {"schema_version": "2025.07-1", "steps": []}

        result = migration_0000.migrate_forward(doc)

        assert result["schema_version"] == 0
        # Original should not be modified
        assert doc["schema_version"] == "2025.07-1"

    def test_0000_migrate_forward_identity_at_version_0(self, migration_0000):
        """migrate_forward is identity when schema_version is already 0."""
        doc = {"schema_version": 0, "steps": []}

        result = migration_0000.migrate_forward(doc)

        assert result["schema_version"] == 0
        # Original should not be modified
        assert doc["schema_version"] == 0

    def test_0000_migrate_forward_fails_on_unexpected_version(self, migration_0000):
        """migrate_forward raises TypeError if version is not calendar and not 0."""
        doc = {"schema_version": 1, "steps": []}

        with pytest.raises(TypeError) as exc_info:
            migration_0000.migrate_forward(doc)

        assert "Expected schema_version" in str(exc_info.value)


class TestMigration0000TargetSchema:
    """Verify target_schema() is hard-coded correctly (v0 baseline)."""

    def test_target_schema_is_frozen(self, migration_0000):
        """target_schema() returns consistent hard-coded snapshot."""
        schema1 = migration_0000.target_schema()
        schema2 = migration_0000.target_schema()
        
        assert schema1 == schema2
        assert schema1["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_target_schema_has_version_0_default(self, migration_0000):
        """target_schema() schema_version should default to 0 (baseline version)."""
        schema = migration_0000.target_schema()
        
        assert "schema_version" in schema["properties"]
        assert schema["properties"]["schema_version"]["default"] == 0
        assert schema["properties"]["schema_version"]["type"] == "integer"
        assert schema["properties"]["schema_version"]["minimum"] == 0

    def test_target_schema_has_required_fields(self, migration_0000):
        """target_schema() includes all required fields."""
        schema = migration_0000.target_schema()
        
        # Top-level required fields
        assert "schema_version" in schema["required"]
        assert "steps" in schema["required"]
        
        # Has definitions
        assert "$defs" in schema
        assert "step" in schema["$defs"]
        assert "question" in schema["$defs"]


class TestMigration0000NoBackwardSupport:
    """Verify 0000 is forward-only (no backward migration)."""
    
    def test_0000_has_no_migrate_backward_function(self, migration_0000):
        """Verify migration 0000 does not have migrate_backward (forward-only)."""
        assert not hasattr(migration_0000, 'migrate_backward')
    
    def test_0000_has_no_previous_schema_function(self, migration_0000):
        """Verify migration 0000 does not have previous_schema (forward-only)."""
        assert not hasattr(migration_0000, 'previous_schema')


class TestMigration0000TransformPreserves:
    """Verify migration only changes schema_version, nothing else."""

    def test_migrate_forward_changes_only_version(self, migration_0000):
        """Forward migration must change ONLY schema_version field."""
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
        
        result = migration_0000.migrate_forward(doc)
        
        # All fields except schema_version must be identical
        assert result["schema_version"] == 0
        assert result["steps"] == doc["steps"]
        
        # Verify deep equality of nested structure
        for key in doc:
            if key != "schema_version":
                assert result[key] == doc[key]


class TestMigration0000Idempotency:
    """Verify 0000 forward is idempotent at v0 (already migrated)."""

    def test_forward_idempotent_at_version_0(self, migration_0000):
        """Apply forward multiple times is idempotent at v0."""
        doc = {
            "schema_version": 0,
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # Forward: 0 → 0 (identity at baseline)
        forward_result = migration_0000.migrate_forward(deepcopy(doc))
        assert forward_result["schema_version"] == 0
        
        # Apply forward again - should remain v0 (idempotent)
        forward_result2 = migration_0000.migrate_forward(deepcopy(forward_result))
        
        # Must match previous result
        assert forward_result2 == forward_result
        assert forward_result2["schema_version"] == 0

    def test_forward_calendar_then_forward_again_idempotent(self, migration_0000):
        """Forward transform is idempotent: apply twice gives same result."""
        doc_calendar = {
            "schema_version": "2025.07-1",
            "steps": [{"title": "S", "description": "", "sections": []}],
        }
        
        # First forward: calendar → v0
        result1 = migration_0000.migrate_forward(deepcopy(doc_calendar))
        assert result1["schema_version"] == 0
        
        # Second forward: v0 → v0 (identity)
        result2 = migration_0000.migrate_forward(deepcopy(result1))
        
        # Both results should be identical
        assert result2 == result1
