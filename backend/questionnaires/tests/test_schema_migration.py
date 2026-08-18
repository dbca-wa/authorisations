"""Unit tests for questionnaire schema migration framework.

Phase 2: Tests verify that QuestionnaireSerialiser enforces strict schema version
validation at write time, and provides actionable error messages for old versions.

Phase 3: Tests verify that the migration infrastructure (loader, utilities) works
correctly for discovering, validating, and applying schema transformations.

Note: Migration-specific tests (for 0001_initial.py transforms, hard-coded schemas,
idempotency, etc.) are in test_schema_migration_0001.py. This module focuses on
infrastructure (loader, path finding, validation utility).
"""

import pytest
from rest_framework.exceptions import ValidationError

from questionnaires.models import QuestionnaireSerialiser
from questionnaires.schema import SCHEMA_VERSION
from questionnaires.schema_migrations_loader import (
    get_migration,
    list_migrations,
    find_path,
)
from questionnaires.schema_migration_utils import validate_transform


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _document():
    """Return a valid questionnaire document with current schema version."""
    return {
        "schema_version": SCHEMA_VERSION,
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
                                "label": "Question 1",
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


def test_questionnaire_serialiser_validate_document_accepts_current_schema_version():
    """Accept documents with schema_version matching current SCHEMA_VERSION constant."""
    serializer = QuestionnaireSerialiser()
    valid_doc = _document()

    # Should not raise ValidationError
    result = serializer.validate_document(valid_doc)

    assert result["schema_version"] == SCHEMA_VERSION


def test_questionnaire_serialiser_validate_document_rejects_mismatched_version():
    """Reject documents with mismatched schema_version and provide actionable error guidance.

    Verifies that:
    - Old schema versions are rejected
    - Error message includes what version is required
    - Error message includes what version was provided
    - Error message includes the migration command to run
    """
    serializer = QuestionnaireSerialiser()
    old_doc = _document()
    old_doc["schema_version"] = "0"  # Old version

    with pytest.raises(ValidationError) as exc_info:
        serializer.validate_document(old_doc)

    error_message = str(exc_info.value.detail[0])

    # Verify error message is actionable
    assert f"'{SCHEMA_VERSION}'" in error_message  # Required version
    assert "'0'" in error_message  # Provided version
    assert "python manage.py schema_migrate_questionnaire" in error_message  # Migration command
    assert "schema version" in error_message.lower()


def test_questionnaire_serialiser_validate_document_rejects_edge_cases():
    """Reject documents with null, missing, or non-dict schema_version values.

    Verifies edge cases are handled gracefully:
    - null schema_version
    - missing schema_version
    - non-dict input values (string, list, etc.)
    """
    serializer = QuestionnaireSerialiser()

    # Test null schema_version
    null_doc = _document()
    null_doc["schema_version"] = None

    with pytest.raises(ValidationError):
        serializer.validate_document(null_doc)

    # Test missing schema_version
    missing_doc = _document()
    del missing_doc["schema_version"]

    with pytest.raises(ValidationError):
        serializer.validate_document(missing_doc)

    # Test non-dict inputs (string)
    with pytest.raises(ValidationError):
        serializer.validate_document("not a dict")

    # Test non-dict inputs (list)
    with pytest.raises(ValidationError):
        serializer.validate_document([])


# ============================================================================
# PHASE 3: Migration Infrastructure Tests
# ============================================================================


class TestMigrationLoader:
    """Test migration file discovery and loading (schema_migrations_loader.py)."""

    def test_get_migration_loads_0001_initial(self):
        """Load migration 0001 and verify it has required components."""
        migration = get_migration("0001")

        assert hasattr(migration, "SCHEMA_VERSION")
        assert migration.SCHEMA_VERSION == "1"
        assert hasattr(migration, "previous_schema")
        assert hasattr(migration, "target_schema")
        assert hasattr(migration, "migrate_forward")
        assert hasattr(migration, "migrate_backward")

    def test_get_migration_missing_raises_error(self):
        """Raise FileNotFoundError when migration number not found."""
        with pytest.raises(FileNotFoundError):
            get_migration("9999")

    def test_list_migrations_includes_0001(self):
        """list_migrations() returns available migration numbers."""
        migrations = list_migrations()

        assert "0001" in migrations
        assert isinstance(migrations, list)
        # Should be sorted
        assert migrations == sorted(migrations)

    def test_find_path_forward_0001_to_0001(self):
        """Find path from 0001 to itself returns single element."""
        path = find_path("0001", "0001")

        assert path == ["0001"]

    def test_find_path_raises_on_missing_migration(self):
        """Raise ValueError when trying to find path with non-existent migration."""
        with pytest.raises(ValueError):
            find_path("0001", "9999")

        with pytest.raises(ValueError):
            find_path("9999", "0001")


class TestValidationUtility:
    """Test validation utility for schema transforms."""

    def test_validate_transform_accepts_valid_doc(self):
        """validate_transform returns (True, []) for valid document."""
        migration = get_migration("0001")
        doc = {
            "schema_version": SCHEMA_VERSION,
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
            "2025.07-1",
            SCHEMA_VERSION,
            migration.previous_schema(),
            migration.target_schema(),
        )

        assert is_valid is True
        assert errors == []

    def test_validate_transform_rejects_wrong_version(self):
        """validate_transform rejects document with mismatched version."""
        migration = get_migration("0001")
        doc = {
            "schema_version": "0",  # Wrong version
            "steps": [],
        }

        is_valid, errors = validate_transform(
            doc,
            "2025.07-1",
            SCHEMA_VERSION,
            migration.previous_schema(),
            migration.target_schema(),
        )

        assert is_valid is False
        assert len(errors) > 0
        assert any("schema_version" in str(e).lower() for e in errors)

    def test_validate_transform_rejects_non_dict(self):
        """validate_transform rejects non-dict inputs."""
        migration = get_migration("0001")
        is_valid, errors = validate_transform(
            "not a dict",
            "1",
            "2",
            migration.previous_schema(),
            migration.target_schema(),
        )

        assert is_valid is False
        assert len(errors) > 0
        assert "must be a dict" in errors[0]

