"""Unit tests for questionnaire schema migration framework (Phase 2).

Tests verify that QuestionnaireSerialiser enforces strict schema version
validation at write time, and provides actionable error messages for old versions.
"""

import pytest
from rest_framework.exceptions import ValidationError

from questionnaires.models import QuestionnaireSerialiser
from questionnaires.schema import SCHEMA_VERSION


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
