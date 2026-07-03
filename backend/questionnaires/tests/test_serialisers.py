"""Unit tests for questionnaire serialisers and schema helpers."""

import pytest

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
        "schema_version": "2025.07-1",
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


def test_reference_field_converter_builds_expected_ref_path():
    """Convert custom reference fields into $defs references for generated JSON schema."""
    reference_field = ReferenceField(definition="question")

    converted = ReferenceFieldConverter().convert(reference_field)

    assert converted == {"$ref": "#/$defs/question"}
