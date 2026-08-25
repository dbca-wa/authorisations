"""Unit tests for questionnaire schema migration framework.

Phase 3: Tests verify that the migration infrastructure (loader, utilities) works
correctly for discovering, validating, and applying schema transformations.

Infrastructure includes:
- Migration file discovery and loading (schema_migrations_loader.py)
- Path finding for forward/backward migrations
- Validation utility for schema transforms
- Database schema version detection with consistency checks
- Version/migration number conversion utilities

Migration-specific tests (for 0001_initial.py transforms, hard-coded schemas,
idempotency, etc.) are in test_schema_migration_0001.py.

Serialiser validation tests are in test_serialisers.py.
"""

from pathlib import Path

import pytest

from questionnaires.schema_migration_utils import (
    get_db_schema_version,
    validate_transform,
)
from questionnaires.schema_migrations_loader import (
    find_path,
    get_migration,
    list_migrations,
    migration_number_to_version,
    version_to_migration_number,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


# ============================================================================
# PHASE 3: Migration Infrastructure Tests
# ============================================================================


class TestMigrationLoader:
    """Test migration file discovery and loading (schema_migrations_loader.py)."""

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_all_migrations_have_required_components(self, migration_number):
        """Verify every migration file has all required functions.
        
        This catches common errors when adding new migrations:
        - Misspelled function names (migrate_backwards vs migrate_backward)
        - Missing rollback function (migrate_backward)
        - Missing schema frozen snapshots
        
        Each migration must define:
        - previous_schema(): callable returning dict (frozen schema before migration)
        - target_schema(): callable returning dict (frozen schema after migration)
        - migrate_forward(doc): callable to transform document forward
        - migrate_backward(doc): callable to transform document backward
        
        Schema version is derived from migration file prefix (e.g., 0001 → 1).
        """
        migration = get_migration(migration_number)

        # Check schema functions
        assert callable(getattr(migration, "previous_schema", None)), \
            f"Migration {migration_number} missing previous_schema() function"
        assert callable(getattr(migration, "target_schema", None)), \
            f"Migration {migration_number} missing target_schema() function"

        # Check transform functions
        assert callable(getattr(migration, "migrate_forward", None)), \
            f"Migration {migration_number} missing migrate_forward() function"
        assert callable(getattr(migration, "migrate_backward", None)), \
            f"Migration {migration_number} missing migrate_backward() function"

        # Verify schemas are dicts
        previous = migration.previous_schema()
        target = migration.target_schema()
        assert isinstance(previous, dict), \
            f"Migration {migration_number} previous_schema() must return dict"
        assert isinstance(target, dict), \
            f"Migration {migration_number} target_schema() must return dict"

    def test_get_migration_missing_raises_error(self):
        """Raise FileNotFoundError when migration number not found."""
        with pytest.raises(FileNotFoundError):
            get_migration("9999")

    def test_list_migrations_returns_sorted_list(self):
        """list_migrations() returns available migration numbers sorted."""
        migrations = list_migrations()

        assert "0001" in migrations
        assert isinstance(migrations, list)
        # Should be sorted
        assert migrations == sorted(migrations)

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_get_migration_can_load_all_available_migrations(self, migration_number):
        """get_migration() can load any migration returned by list_migrations()."""
        migration = get_migration(migration_number)
        assert migration is not None

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_find_path_forward_migration_to_itself(self, migration_number):
        """Find forward path from any migration to itself returns single element."""
        path = find_path(migration_number, migration_number)
        assert path == [migration_number]

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_find_path_backward_migration_to_itself(self, migration_number):
        """Find backward path (rollback) from any migration to itself returns single element."""
        path = find_path(migration_number, migration_number)
        assert path == [migration_number]

    def test_find_path_raises_on_missing_migration(self):
        """Raise ValueError when trying to find path with non-existent migration."""
        with pytest.raises(ValueError):
            find_path("0001", "9999")

        with pytest.raises(ValueError):
            find_path("9999", "0001")

    def test_get_migration_raises_on_duplicate_migration_files(self, monkeypatch):
        """Raise RuntimeError if multiple migration files exist with same number.
        
        This catches the scenario where a developer accidentally creates both
        0001_initial.py and 0001_alternate.py in the same directory.
        Without this check, the loader silently picks the first one found,
        leading to unpredictable behavior.
        """
        # Patch Path.glob to return 2 matching files
        def mock_glob(self, pattern):
            if pattern.startswith("0001_"):
                # Return 2 mock files for 0001_*.py pattern
                mock_file1 = Path("/fake/0001_v1.py")
                mock_file2 = Path("/fake/0001_v2.py")
                return [mock_file1, mock_file2]
            return []
        
        monkeypatch.setattr(Path, "glob", mock_glob)
        
        # Now call get_migration with the real function
        # It should raise RuntimeError for 2 matching files
        with pytest.raises(RuntimeError) as exc_info:
            get_migration("0001")
        
        error_msg = str(exc_info.value)
        assert "0001" in error_msg
        assert ("2" in error_msg or "duplicate" in error_msg.lower())
        assert "exactly 1" in error_msg.lower()


class TestVersionConversion:
    """Test bidirectional version/migration number conversion utilities."""

    @pytest.mark.parametrize("migration_number,expected_version", [
        ("0001", 1),
        ("0002", 2),
        ("0010", 10),
        ("0100", 100),
        ("9999", 9999),
    ])
    def test_migration_number_to_version_converts_correctly(
        self, migration_number, expected_version
    ):
        """Verify migration_number_to_version converts "NNNN" → N correctly."""
        result = migration_number_to_version(migration_number)
        assert result == expected_version
        assert isinstance(result, int)

    @pytest.mark.parametrize("version,expected_migration", [
        (1, "0001"),
        (2, "0002"),
        (10, "0010"),
        (100, "0100"),
        (9999, "9999"),
    ])
    def test_version_to_migration_number_converts_correctly(
        self, version, expected_migration
    ):
        """Verify version_to_migration_number converts N → "NNNN" with zero-padding."""
        result = version_to_migration_number(version)
        assert result == expected_migration
        assert isinstance(result, str)
        assert len(result) == 4

    @pytest.mark.parametrize("invalid_input", [
        "abcd",
        "00ab",
        "123a",
        "",
        "not_a_number",
    ])
    def test_migration_number_to_version_raises_on_invalid_input(self, invalid_input):
        """Verify migration_number_to_version raises ValueError for non-numeric input."""
        with pytest.raises(ValueError):
            migration_number_to_version(invalid_input)

    def test_version_to_migration_number_zero_pads(self):
        """Verify version_to_migration_number produces 4-digit zero-padded strings."""
        assert version_to_migration_number(0) == "0000"
        assert version_to_migration_number(5) == "0005"
        assert version_to_migration_number(42) == "0042"


class TestValidationUtility:
    """Test validation utility for schema transforms."""

    def test_validate_transform_accepts_valid_doc(self):
        """validate_transform returns (True, []) for valid document matching frozen migration schema.
        
        Tests with migration 0001's frozen target schema (version 1).
        This validation is independent of the current production schema version, which may
        differ as new migrations are added. The test verifies that validate_transform correctly
        checks document structure against the frozen schema passed from a migration file.
        
        When adding migration 0002 with a different target schema, add a new migration-specific
        test using that migration's frozen schemas.
        """
        migration = get_migration("0001")
        target_version = migration_number_to_version("0001")
        doc = {
            "schema_version": target_version,
            "steps": [
                {
                    "title": "Step 1",
                    "description": "",
                    "sections": [
                        {
                            "title": "Section 1",
                            "description": "",
                            "questions": [
                                {
                                    "label": "Q1",
                                    "type": "text",
                                    "is_required": False,
                                    "description": "",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        is_valid, errors = validate_transform(
            doc,
            "0000",  # Previous version (not validated against doc)
            target_version,  # Must match doc's schema_version
            migration.previous_schema(),
            migration.target_schema(),
        )

        assert is_valid is True
        assert errors == []

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_validate_transform_rejects_wrong_version_for_all_migrations(self, migration_number):
        """validate_transform rejects document with mismatched version for any migration.
        
        Tests that version validation is the first check, regardless of migration.
        """
        migration = get_migration(migration_number)
        target_version = migration_number_to_version(migration_number)
        # Create a minimal doc - we're testing version checking, not structure
        doc = {"schema_version": "wrong_version"}
        
        is_valid, errors = validate_transform(
            doc,
            "ignored_old_version",
            target_version,  # Expect this version
            migration.previous_schema(),
            migration.target_schema(),
        )
        
        assert is_valid is False, f"Migration {migration_number} should reject wrong version"
        assert len(errors) > 0
        assert any("schema_version" in str(e).lower() for e in errors)

    @pytest.mark.parametrize("migration_number", list_migrations())
    def test_validate_transform_rejects_non_dict_for_all_migrations(self, migration_number):
        """validate_transform rejects non-dict inputs for any migration."""
        migration = get_migration(migration_number)
        target_version = migration_number_to_version(migration_number)
        is_valid, errors = validate_transform(
            "not a dict",
            "0",
            target_version,
            migration.previous_schema(),
            migration.target_schema(),
        )
        
        assert is_valid is False, f"Migration {migration_number} should reject non-dict"
        assert len(errors) > 0
        assert "must be a dict" in errors[0]


class TestDatabaseSchemaVersionDetection:
    """Test database schema version detection and consistency checking.
    
    Critical tests for catching migration precondition failures that would
    otherwise silently corrupt data.
    """

    def test_get_db_schema_version_empty_database(self):
        """Empty database returns None."""
        result = get_db_schema_version()
        assert result is None

    def test_get_db_schema_version_single_uniform_version(self, questionnaire_factory):
        """All records at same version returns that version."""
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        
        result = get_db_schema_version()
        assert result == 1

    def test_get_db_schema_version_raises_on_mixed_versions(self, questionnaire_factory):
        """Mixed versions raise RuntimeError (critical safety check).
        
        This test catches the scenario where a failed migration leaves records
        in an inconsistent state. Without this check, subsequent migrations
        could silently corrupt data.
        """
        # Simulate a failed/partial migration: some at 1, some at 2
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        questionnaire_factory(document={"schema_version": 2, "steps": []})
        
        # Should raise RuntimeError, not silently vote for majority
        with pytest.raises(RuntimeError) as exc_info:
            get_db_schema_version()
        
        error_msg = str(exc_info.value)
        # Error should identify the inconsistent state
        assert "multiple schema versions" in error_msg.lower()

    def test_get_db_schema_version_error_includes_version_counts(self, questionnaire_factory):
        """RuntimeError message includes version distribution for debugging."""
        # Create imbalanced mixed state: 5 at 1, 2 at 2
        for _ in range(5):
            questionnaire_factory(document={"schema_version": 1, "steps": []})
        for _ in range(2):
            questionnaire_factory(document={"schema_version": 2, "steps": []})
        
        with pytest.raises(RuntimeError) as exc_info:
            get_db_schema_version()
        
        error_msg = str(exc_info.value)
        # Should show version counts for debugging
        assert "1" in error_msg
        assert "2" in error_msg

    def test_get_db_schema_version_returns_string_type(self, questionnaire_factory):
        """Return type is always int for integer schema versions."""
        questionnaire_factory(document={"schema_version": 1, "steps": []})
        
        result = get_db_schema_version()
        
        assert isinstance(result, int), f"Expected int, got {type(result).__name__}"
        assert result == 1

    def test_get_db_schema_version_numeric_ordering_with_multi_digit_versions(self, questionnaire_factory):
        """Version ordering is numeric with integer versions.
        
        With integer versions, ordering is naturally: 1, 2, 3, 10, 11, 12
        """
        # Create versions in random order
        versions_to_create = [2, 10, 1, 11, 3]
        for version in versions_to_create:
            questionnaire_factory(document={"schema_version": version, "steps": []})
        
        # Add one more version to trigger mixed-version error
        questionnaire_factory(document={"schema_version": 2, "steps": []})
        
        with pytest.raises(RuntimeError) as exc_info:
            get_db_schema_version()
        
        error_msg = str(exc_info.value)
        # Should show all versions were detected
        for version in set(versions_to_create):
            assert str(version) in error_msg, f"Version {version} should be in error message"

