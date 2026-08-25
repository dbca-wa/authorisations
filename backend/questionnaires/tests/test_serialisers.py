"""Unit tests for questionnaire serialisers and schema helpers."""

import pytest
from rest_framework.exceptions import ValidationError

from questionnaires.models import Questionnaire, QuestionnaireSerialiser
from questionnaires.serialisers import (
    GridQuestionColumnSerialiser,
    QuestionSerialiser,
    ReferenceField,
    ReferenceFieldConverter,
    SectionSerialiser,
    StepSerialiser,
)


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _document():
    """Return a valid questionnaire document for serializer representation tests."""
    return {
        "schema_version": 1,
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


def test_questionnaire_model_serialiser_exposes_process_slug(process, user):
    """Expose process_slug so clients can route questionnaires under process identity."""
    questionnaire = Questionnaire.objects.create(
        process=process,
        code="new",
        name="New application",
        description="Description",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    data = QuestionnaireSerialiser(questionnaire).data

    assert data["process_slug"] == process.slug
    assert data["code"] == "new"


def test_questionnaire_model_serialiser_exposes_process_name(process, user):
    """Expose process_name so clients can display the process name without additional API calls."""
    questionnaire = Questionnaire.objects.create(
        process=process,
        code="new",
        name="New application",
        description="Description",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    data = QuestionnaireSerialiser(questionnaire).data

    assert data["process_name"] == process.name
    assert data["process_slug"] == process.slug


def test_question_serialiser_defaults_is_required_to_false():
    """Default optional questions to is_required=False to avoid null boolean schema values."""
    serialiser = QuestionSerialiser(
        data={
            "label": "Question 1",
            "type": "text",
            "description": "",
        }
    )

    assert serialiser.is_valid(), serialiser.errors
    assert serialiser.validated_data["is_required"] is False


def test_question_serialiser_rejects_unknown_question_type():
    """Reject unsupported question types so document schema stays bounded."""
    serialiser = QuestionSerialiser(
        data={
            "label": "Question 1",
            "type": "unsupported",
        }
    )

    assert not serialiser.is_valid()
    assert "type" in serialiser.errors


def test_grid_question_column_serialiser_rejects_unknown_column_type():
    """Restrict grid column types to known options for consistent answer rendering."""
    serialiser = GridQuestionColumnSerialiser(
        data={
            "label": "Column A",
            "type": "unsupported",
        }
    )

    assert not serialiser.is_valid()
    assert "type" in serialiser.errors


def test_section_serialiser_requires_at_least_one_question():
    """Require non-empty question lists to prevent empty sections in questionnaire documents."""
    serialiser = SectionSerialiser(
        data={
            "title": "Section 1",
            "description": "",
            "questions": [],
        }
    )

    assert not serialiser.is_valid()
    assert "questions" in serialiser.errors


def test_step_serialiser_requires_at_least_one_section():
    """Require non-empty section lists so each step has actionable content."""
    serialiser = StepSerialiser(
        data={
            "title": "Step 1",
            "description": "",
            "sections": [],
        }
    )

    assert not serialiser.is_valid()
    assert "sections" in serialiser.errors


def test_questionnaire_serialiser_validate_document_accepts_current_schema_version():
    """Accept documents with schema_version matching document structure."""
    serialiser = QuestionnaireSerialiser()
    valid_doc = _document()

    # Should not raise ValidationError
    result = serialiser.validate_document(valid_doc)

    assert result["schema_version"] == valid_doc["schema_version"]


def test_questionnaire_serialiser_validate_document_rejects_mismatched_version():
    """Reject documents with mismatched schema_version and provide actionable error guidance.

    Verifies that:
    - Old schema versions are rejected
    - Error message includes what version is required
    - Error message includes what version was provided
    - Error message includes the migration command to run
    """
    serialiser = QuestionnaireSerialiser()
    old_doc = _document()
    old_doc["schema_version"] = "0"  # Old version

    with pytest.raises(ValidationError) as exc_info:
        serialiser.validate_document(old_doc)

    error_message = str(exc_info.value.detail[0])

    # Verify error message is actionable
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
    serialiser = QuestionnaireSerialiser()

    # Test null schema_version
    null_doc = _document()
    null_doc["schema_version"] = None

    with pytest.raises(ValidationError):
        serialiser.validate_document(null_doc)

    # Test missing schema_version
    missing_doc = _document()
    del missing_doc["schema_version"]

    with pytest.raises(ValidationError):
        serialiser.validate_document(missing_doc)

    # Test non-dict inputs (string)
    with pytest.raises(ValidationError):
        serialiser.validate_document("not a dict")

    # Test non-dict inputs (list)
    with pytest.raises(ValidationError):
        serialiser.validate_document([])


def test_reference_field_converter_builds_expected_ref_path():
    """Convert custom reference fields into $defs references for generated JSON schema."""
    reference_field = ReferenceField(definition="question")

    converted = ReferenceFieldConverter().convert(reference_field)

    assert converted == {"$ref": "#/$defs/question"}
