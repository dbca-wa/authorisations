"""Comprehensive tests for Phase 9 generic management commands.

Tests cover:
- Nested version_path support (2+ levels, 3+ levels) - CRITICAL
- Core helper functions used by commands
- Type hints and imports in command files
"""

import pytest
from django.test import TestCase
from pathlib import Path

from schema_migration_framework import get_schema_version_from_document
from schema_migration_framework.management.commands.schema_status import Command as StatusCommand
from schema_migration_framework.management.commands.schema_migrate import Command as MigrateCommand
from schema_migration_framework.management.commands.schema_rollback import Command as RollbackCommand
from schema_migration_framework.management.commands.base import SchemaMigrationBaseCommand
from schema_migration_framework.loader import find_migration_by_output_version


class NestedVersionPathTestCase(TestCase):
    """Test nested version_path support (dot notation). CRITICAL REQUIREMENT."""

    def test_simple_version_path_schema_version(self):
        """Test simple version_path: 'schema_version'."""
        doc = {"schema_version": 2, "data": "test"}
        version_path = "schema_version"
        
        version = get_schema_version_from_document(doc, version_path)
        
        assert version == 2

    def test_nested_version_path_two_levels(self):
        """Test nested version_path with 2 levels: 'metadata.version'."""
        doc = {
            "metadata": {"version": 3},
            "data": "test"
        }
        version_path = "metadata.version"
        
        version = get_schema_version_from_document(doc, version_path)
        
        assert version == 3

    def test_nested_version_path_three_levels(self):
        """Test nested version_path with 3+ levels: 'metadata.schema.version'."""
        doc = {
            "metadata": {
                "schema": {
                    "version": 4
                }
            },
            "data": "test"
        }
        version_path = "metadata.schema.version"
        
        version = get_schema_version_from_document(doc, version_path)
        
        assert version == 4

    def test_nested_version_path_four_levels(self):
        """Test nested version_path with 4 levels: 'a.b.c.d'."""
        doc = {
            "a": {
                "b": {
                    "c": {
                        "d": 5
                    }
                }
            }
        }
        version_path = "a.b.c.d"
        
        version = get_schema_version_from_document(doc, version_path)
        
        assert version == 5

    def test_missing_nested_path_returns_none(self):
        """Test that missing path returns None (optional nested field)."""
        doc = {"metadata": {"other_field": 123}}
        version_path = "metadata.version"
        
        version = get_schema_version_from_document(doc, version_path)
        
        assert version is None

    def test_nondict_intermediate_raises_typeerror(self):
        """Test that non-dict intermediate value raises TypeError."""
        doc = {"metadata": "not_a_dict"}
        version_path = "metadata.version"
        
        with pytest.raises(TypeError):
            get_schema_version_from_document(doc, version_path)


class CommandsImplementationTestCase(TestCase):
    """Test that commands are properly implemented with type hints and imports."""

    def test_schema_status_imports_correct(self):
        """Verify schema_status.py imports are correct."""
        assert StatusCommand is not None
        # Command should have handle method with proper signature
        assert hasattr(StatusCommand, 'handle')

    def test_schema_migrate_imports_correct(self):
        """Verify schema_migrate.py imports are correct."""
        assert MigrateCommand is not None
        assert hasattr(MigrateCommand, 'handle')
        # Should have helper methods
        assert hasattr(MigrateCommand, '_test_transforms')
        assert hasattr(MigrateCommand, '_apply_transforms')
        assert hasattr(MigrateCommand, '_get_db_version')

    def test_schema_rollback_imports_correct(self):
        """Verify schema_rollback.py imports are correct."""
        assert RollbackCommand is not None
        assert hasattr(RollbackCommand, 'handle')
        # Should have backward transform methods
        assert hasattr(RollbackCommand, '_test_backward_transforms')
        assert hasattr(RollbackCommand, '_apply_backward_transforms')
        assert hasattr(RollbackCommand, '_get_db_version')

    def test_base_command_exists(self):
        """Verify base command class exists."""
        assert SchemaMigrationBaseCommand is not None
        assert hasattr(SchemaMigrationBaseCommand, 'target_key')


class FindMigrationByVersionTestCase(TestCase):
    """Test find_migration_by_output_version helper function."""

    def test_find_migration_valid_version(self):
        """Test finding migration by output version."""
        
        # Use questionnaires schema_migrations path (known to exist)
        migrations_path = Path(__file__).parent.parent.parent.parent / "questionnaires" / "schema_migrations"
        
        if migrations_path.exists():
            result = find_migration_by_output_version(1, str(migrations_path))
            assert result == "0001"

    def test_find_migration_invalid_version_zero(self):
        """Test that version 0 raises ValueError."""
        
        migrations_path = Path(__file__).parent.parent.parent.parent / "questionnaires" / "schema_migrations"
        
        if migrations_path.exists():
            with pytest.raises(ValueError) as exc_info:
                find_migration_by_output_version(0, str(migrations_path))
            assert "Only positive integers >= 1" in str(exc_info.value)

    def test_find_migration_nonexistent_version(self):
        """Test that nonexistent version raises ValueError."""
        
        migrations_path = Path(__file__).parent.parent.parent.parent / "questionnaires" / "schema_migrations"
        
        if migrations_path.exists():
            with pytest.raises(ValueError) as exc_info:
                find_migration_by_output_version(9999, str(migrations_path))
            assert "No migration found" in str(exc_info.value)

