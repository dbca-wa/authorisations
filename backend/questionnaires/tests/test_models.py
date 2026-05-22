"""Unit tests for questionnaire model invariants."""

import pytest
from django.db import IntegrityError

from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _document():
    """Return a minimal valid questionnaire document payload for test rows."""
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


def test_questionnaire_str_representation_uses_name_code_version_and_process(process, user):
    """Render questionnaire rows with enough detail to identify lineage and version."""
    questionnaire = Questionnaire.objects.create(
        process=process,
        code="new",
        name="New application",
        description="Description",
        version=2,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    assert str(questionnaire) == 'Questionnaire "New application" [new] (v2) for s40'


def test_questionnaire_default_ordering_is_process_code_then_version_desc(process, user):
    """Keep questionnaire lineage ordering deterministic for versioned queries."""
    process_b = AuthorisationProcess.objects.create(
        slug="b",
        name="Process B",
        description="Second process",
        sort_order=2,
    )

    first = Questionnaire.objects.create(
        process=process,
        code="new",
        name="New v1",
        description="Description",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )
    second = Questionnaire.objects.create(
        process=process,
        code="new",
        name="New v2",
        description="Description",
        version=2,
        document=_document(),
        sort_order=1,
        created_by=user,
    )
    third = Questionnaire.objects.create(
        process=process_b,
        code="new",
        name="Other process",
        description="Description",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    ordered_ids = list(Questionnaire.objects.values_list("id", flat=True))

    assert ordered_ids == [second.id, first.id, third.id]


def test_questionnaire_unique_constraint_blocks_same_process_code_and_version(process, user):
    """Prevent duplicate version rows within a process/code lineage."""
    Questionnaire.objects.create(
        process=process,
        code="renewal",
        name="Renewal v1",
        description="Description",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    with pytest.raises(IntegrityError):
        Questionnaire.objects.create(
            process=process,
            code="renewal",
            name="Renewal v1 duplicate",
            description="Description",
            version=1,
            document=_document(),
            sort_order=2,
            created_by=user,
        )
