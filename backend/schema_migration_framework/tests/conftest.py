"""Pytest configuration and shared fixtures for schema migration framework tests."""

import pytest
from unittest.mock import MagicMock
from types import ModuleType


def create_mock_migration(
    from_version: int,
    to_version: int,
    name: str = None,
) -> ModuleType:
    """Create a mock migration module with proper transform functions.
    
    Args:
        from_version: Schema version this migration transforms FROM.
        to_version: Schema version this migration transforms TO.
        name: Optional name for the migration.
    
    Returns:
        Mock migration module with previous_schema(), target_schema(),
        migrate_forward(), and migrate_backward() functions.
    """
    if name is None:
        name = f"mock_migration_{from_version}_to_{to_version}"
    
    migration = ModuleType(name)
    
    # Define schema structures
    def previous_schema():
        """Return schema for version {from_version}."""
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer", "default": from_version},
                "steps": {"type": "array", "default": []},
            },
        }
    
    def target_schema():
        """Return schema for version {to_version}."""
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer", "default": to_version},
                "steps": {"type": "array", "default": []},
            },
        }
    
    def migrate_forward(document: dict) -> dict:
        """Transform document from v{from_version} to v{to_version}."""
        doc = document.copy()
        doc["schema_version"] = to_version
        # Add a transform marker so we can verify migration occurred
        doc[f"_transformed_by_v{to_version}"] = True
        return doc
    
    def migrate_backward(document: dict) -> dict:
        """Transform document from v{to_version} back to v{from_version}."""
        doc = document.copy()
        doc["schema_version"] = from_version
        # Remove the forward transform marker
        doc.pop(f"_transformed_by_v{to_version}", None)
        return doc
    
    # Attach functions to module
    migration.previous_schema = previous_schema
    migration.target_schema = target_schema
    migration.migrate_forward = migrate_forward
    migration.migrate_backward = migrate_backward
    
    return migration


@pytest.fixture
def mock_migrations_0_to_4():
    """Fixture providing 5 mock migrations (0->1, 1->2, 2->3, 3->4, 4->5).
    
    These represent a migration path from schema version 0 to 4.
    Each migration transforms the schema_version field and adds markers.
    """
    return {
        "0001": create_mock_migration(0, 1, "0001_initial"),
        "0002": create_mock_migration(1, 2, "0002_v2"),
        "0003": create_mock_migration(2, 3, "0003_v3"),
        "0004": create_mock_migration(3, 4, "0004_v4"),
    }


@pytest.fixture
def mock_migrations_with_0000():
    """Fixture providing mock migrations including 0000 rollback-only migration.
    
    0000 is special: it only supports migrate_backward (v1->v0), not forward.
    """
    migrations = {
        "0001": create_mock_migration(0, 1, "0001_initial"),
        "0002": create_mock_migration(1, 2, "0002_v2"),
        "0003": create_mock_migration(2, 3, "0003_v3"),
        "0004": create_mock_migration(3, 4, "0004_v4"),
    }
    
    # Add 0000 as rollback-only
    rollback_0000 = ModuleType("0000_rollback")
    
    def previous_schema():
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer", "default": 0},
                "steps": {"type": "array", "default": []},
            },
        }
    
    def target_schema():
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer", "default": 1},
                "steps": {"type": "array", "default": []},
            },
        }
    
    def migrate_forward(document: dict) -> dict:
        raise RuntimeError("Rollback migration 0000 does not support forward migration")
    
    def migrate_backward(document: dict) -> dict:
        doc = document.copy()
        doc["schema_version"] = 0
        doc.pop("_transformed_by_v1", None)
        return doc
    
    rollback_0000.previous_schema = previous_schema
    rollback_0000.target_schema = target_schema
    rollback_0000.migrate_forward = migrate_forward
    rollback_0000.migrate_backward = migrate_backward
    
    migrations["0000"] = rollback_0000
    return migrations
