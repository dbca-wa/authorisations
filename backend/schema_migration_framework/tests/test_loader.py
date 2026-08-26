"""Unit tests for schema_migration_framework.loader module."""

from pathlib import Path

import pytest

from schema_migration_framework.loader import (
    get_migration,
    list_migrations,
    migration_number_to_version,
    version_to_migration_number,
)


@pytest.fixture
def fixtures_path():
    """Path to sample migrations fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_migrations"


class TestMigrationNumberConversion:
    """Tests for migration number ↔ version conversion."""

    def test_migration_number_to_version_valid(self):
        """Convert valid migration number to version."""
        assert migration_number_to_version("0001") == 1
        assert migration_number_to_version("0002") == 2
        assert migration_number_to_version("0010") == 10
        assert migration_number_to_version("9999") == 9999

    def test_migration_number_to_version_invalid(self):
        """Reject non-numeric migration numbers."""
        with pytest.raises(ValueError, match="Invalid migration number"):
            migration_number_to_version("00ab")
        with pytest.raises(ValueError, match="Invalid migration number"):
            migration_number_to_version("xyz")

    def test_version_to_migration_number_valid(self):
        """Convert version to zero-padded migration number."""
        assert version_to_migration_number(1) == "0001"
        assert version_to_migration_number(2) == "0002"
        assert version_to_migration_number(10) == "0010"
        assert version_to_migration_number(9999) == "9999"

    def test_version_to_migration_number_roundtrip(self):
        """Roundtrip conversion maintains value."""
        for version in [1, 2, 10, 100, 9999]:
            migration_num = version_to_migration_number(version)
            recovered_version = migration_number_to_version(migration_num)
            assert recovered_version == version


class TestGetMigration:
    """Tests for loading migration modules."""

    def test_get_migration_loads_valid_migration(self, fixtures_path):
        """Load existing migration module."""
        migration = get_migration("0001", str(fixtures_path))
        assert hasattr(migration, "previous_schema")
        assert hasattr(migration, "target_schema")
        assert hasattr(migration, "migrate_forward")
        assert hasattr(migration, "migrate_backward")

    def test_get_migration_returns_callable_functions(self, fixtures_path):
        """Loaded migration has callable functions."""
        migration = get_migration("0001", str(fixtures_path))
        assert callable(migration.previous_schema)
        assert callable(migration.target_schema)
        assert callable(migration.migrate_forward)
        assert callable(migration.migrate_backward)

    def test_get_migration_functions_return_expected_types(self, fixtures_path):
        """Migration functions return expected types."""
        migration = get_migration("0001", str(fixtures_path))
        assert isinstance(migration.previous_schema(), dict)
        assert isinstance(migration.target_schema(), dict)

    def test_get_migration_nonexistent_raises_error(self, fixtures_path):
        """Raise FileNotFoundError for non-existent migration."""
        with pytest.raises(FileNotFoundError, match="Migration 9999 not found"):
            get_migration("9999", str(fixtures_path))

    def test_get_migration_multiple_files_raises_error(self, tmp_path):
        """Raise RuntimeError if multiple files match same number."""
        # Create two files with same migration number
        (tmp_path / "0001_first.py").write_text("")
        (tmp_path / "0001_second.py").write_text("")
        
        with pytest.raises(RuntimeError, match="Expected exactly 1 migration file"):
            get_migration("0001", str(tmp_path))


class TestListMigrations:
    """Tests for discovering available migrations."""

    def test_list_migrations_finds_all_migrations(self, fixtures_path):
        """Discover all available migrations."""
        migrations = list_migrations(str(fixtures_path))
        assert "0001" in migrations
        assert "0002" in migrations
        assert len(migrations) >= 2

    def test_list_migrations_returns_sorted(self, fixtures_path):
        """Migrations are returned in sorted order."""
        migrations = list_migrations(str(fixtures_path))
        assert migrations == sorted(migrations)

    def test_list_migrations_empty_directory(self, tmp_path):
        """Return empty list for directory with no migrations."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        migrations = list_migrations(str(empty_dir))
        assert migrations == []

    def test_list_migrations_nonexistent_directory(self, tmp_path):
        """Return empty list for non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        migrations = list_migrations(str(nonexistent))
        assert migrations == []

    def test_list_migrations_ignores_pycache(self, tmp_path):
        """Ignore __pycache__ and other special files."""
        (tmp_path / "0001_real.py").write_text("")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "0002_fake.py").write_text("")
        
        migrations = list_migrations(str(tmp_path))
        assert migrations == ["0001"]
