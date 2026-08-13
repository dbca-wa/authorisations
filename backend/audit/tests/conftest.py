"""Shared fixtures for audit app tests."""

import pytest
from django.contrib.auth.models import Group
from itertools import count

from applications.models import Application
from applications.statuses import ApplicationStatus
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire


@pytest.fixture
def reviewer_group(db):
    """Create the canonical reviewer group used in review authorisation tests."""
    return Group.objects.get_or_create(name="reviewers")[0]


@pytest.fixture
def process_for_review(db, reviewer_group):
    """Create a process that the reviewer group can review."""
    process = AuthorisationProcess.objects.create(
        slug="audit-test-process",
        name="Audit Test Process",
        description="Process for audit tests",
        sort_order=1,
    )
    process.reviewer_groups.add(reviewer_group)
    return process


@pytest.fixture
def questionnaire_for_review(db, process_for_review, user):
    """Create a questionnaire for the reviewable process."""
    return Questionnaire.objects.create(
        process=process_for_review,
        code="audit-test-form",
        name="Audit Test Form",
        description="Form for audit tests",
        document={
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
        },
        sort_order=1,
        created_by=user,
    )


@pytest.fixture
def audit_application_factory(db, questionnaire_for_review):
    """Return a factory that creates applications for audit testing with proper reviewer authorization."""

    def _create(**overrides):
        values = {
            "questionnaire": questionnaire_for_review,
            "status": ApplicationStatus.DRAFT,
            "document": {
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        }
        values.update(overrides)
        return Application.objects.create(**values)

    return _create
