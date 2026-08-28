"""Unit tests for migration 0001: Applications versioning baseline (0 → 1)."""

import pytest
from copy import deepcopy
import importlib

from schema_migration_framework.loader import get_migration
from schema_migration_framework.executor import get_migrations_package_path


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


# Ensure the schema_migrations package is importable
importlib.import_module("applications.schema_migrations")

# Get migrations package path once for all tests
_MIGRATIONS_PACKAGE_PATH = get_migrations_package_path("applications.schema_migrations")


@pytest.fixture
def migration_0001():
    """Load migration 0001 via generic framework."""
    return get_migration("0001", _MIGRATIONS_PACKAGE_PATH)


class TestMigration0001Transforms:
    """Test migration 0001 forward/backward transforms."""
    
    def test_0001_migrate_forward_upgrades_version_0_to_1(self, migration_0001):
        """migrate_forward upgrades schema_version from 0 to 1."""
        doc = {
            "schema_version": 0,
            "active_step": 1,
            "steps": [
                {
                    "is_valid": True,
                    "answers": {"1-1": "answer1"}
                }
            ]
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        assert result["active_step"] == 1
        assert result["steps"] == doc["steps"]
        # Original should not be modified
        assert doc["schema_version"] == 0
    
    def test_0001_migrate_forward_fails_if_already_version_1(self, migration_0001):
        """migrate_forward raises TypeError if document is already version 1."""
        doc = {
            "schema_version": 1,
            "active_step": 1,
            "steps": []
        }
        
        with pytest.raises(TypeError) as exc_info:
            migration_0001.migrate_forward(doc)
        
        assert "Expected schema_version 0" in str(exc_info.value)
    
    def test_0001_migrate_forward_fails_if_wrong_version(self, migration_0001):
        """migrate_forward raises TypeError if version is not 0."""
        doc = {
            "schema_version": 999,
            "active_step": 1,
            "steps": []
        }
        
        with pytest.raises(TypeError) as exc_info:
            migration_0001.migrate_forward(doc)
        
        assert "Expected schema_version 0" in str(exc_info.value)
    
    def test_0001_migrate_backward_downgrades_version_1_to_0(self, migration_0001):
        """migrate_backward downgrades schema_version from 1 to 0."""
        doc = {
            "schema_version": 1,
            "active_step": 0,
            "steps": [
                {
                    "is_valid": False,
                    "answers": {"2-1": "test"}
                }
            ]
        }
        
        result = migration_0001.migrate_backward(doc)
        
        assert result["schema_version"] == 0
        assert result["active_step"] == 0
        assert result["steps"] == doc["steps"]
        # Original should not be modified
        assert doc["schema_version"] == 1
    
    def test_0001_migrate_backward_fails_if_not_version_1(self, migration_0001):
        """migrate_backward raises TypeError if not at version 1."""
        doc = {
            "schema_version": 0,
            "active_step": 1,
            "steps": []
        }
        
        with pytest.raises(TypeError) as exc_info:
            migration_0001.migrate_backward(doc)
        
        assert "Expected schema_version 1" in str(exc_info.value)


class TestMigration0001Schemas:
    """Verify schema definitions are hard-coded correctly."""
    
    def test_previous_schema_is_frozen(self, migration_0001):
        """previous_schema() returns consistent hard-coded snapshot."""
        schema1 = migration_0001.previous_schema()
        schema2 = migration_0001.previous_schema()
        
        assert schema1 == schema2
        assert schema1["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    
    def test_previous_schema_has_version_0_default(self, migration_0001):
        """previous_schema() schema_version should default to 0."""
        schema = migration_0001.previous_schema()
        
        assert "schema_version" in schema["properties"]
        assert schema["properties"]["schema_version"]["default"] == 0
        assert schema["properties"]["schema_version"]["type"] == "integer"
    
    def test_target_schema_has_version_1_default(self, migration_0001):
        """target_schema() schema_version should default to 1."""
        schema = migration_0001.target_schema()
        
        assert "schema_version" in schema["properties"]
        assert schema["properties"]["schema_version"]["default"] == 1
        assert schema["properties"]["schema_version"]["type"] == "integer"
    
    def test_target_schema_frozen(self, migration_0001):
        """target_schema() returns consistent hard-coded snapshot."""
        schema1 = migration_0001.target_schema()
        schema2 = migration_0001.target_schema()
        
        assert schema1 == schema2


class TestMigration0001Idempotency:
    """Verify transforms are reversible and idempotent."""
    
    def test_forward_then_backward_equals_identity(self, migration_0001):
        """Apply forward then backward returns original."""
        doc = {
            "schema_version": 0,
            "active_step": 2,
            "steps": [
                {"is_valid": True, "answers": {"1-1": "value1"}},
                {"is_valid": False, "answers": {"1-2": "value2"}}
            ]
        }
        
        forward_result = migration_0001.migrate_forward(deepcopy(doc))
        assert forward_result["schema_version"] == 1
        
        backward_result = migration_0001.migrate_backward(deepcopy(forward_result))
        
        assert backward_result == doc
    
    def test_backward_then_forward_equals_identity(self, migration_0001):
        """Apply backward then forward returns original."""
        doc = {
            "schema_version": 1,
            "active_step": 0,
            "steps": [
                {"is_valid": None, "answers": {}}
            ]
        }
        
        backward_result = migration_0001.migrate_backward(deepcopy(doc))
        assert backward_result["schema_version"] == 0
        
        forward_result = migration_0001.migrate_forward(deepcopy(backward_result))
        
        assert forward_result == doc
