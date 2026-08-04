import pytest
from itertools import count
from rest_framework.test import APIClient

from applications.models import Application
from applications.statuses import ApplicationStatus
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User


@pytest.fixture
def api_client():
    """Return a DRF API client for request-level backend tests."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create the canonical applicant used by backend tests."""
    return User.objects.create_user(username="applicant", password="testpass123")


@pytest.fixture
def other_user(db):
    """Create a second applicant to exercise ownership boundaries."""
    return User.objects.create_user(username="other-applicant", password="testpass123")


@pytest.fixture
def process_factory(db):
    """Return a factory that creates authorisation processes with deterministic defaults."""
    sequence = count(1)

    def _create(**overrides):
        index = next(sequence)
        values = {
            "slug": f"proc-{index}",
            "name": f"Process {index}",
            "description": f"Process description {index}",
            "sort_order": index,
        }
        values.update(overrides)
        return AuthorisationProcess.objects.create(**values)

    return _create


@pytest.fixture
def process(db):
    """Create a stable authorisation process fixture for tests that need exactly one."""
    return AuthorisationProcess.objects.create(
        slug="s40",
        name="Section 40",
        description="Section 40 authorisation process",
        sort_order=1,
    )


@pytest.fixture
def questionnaire_factory(db, user, process_factory):
    """Return a factory that creates questionnaires for list/retrieve and versioning tests."""
    sequence = count(1)

    def _create(**overrides):
        index = next(sequence)
        # Use provided process or create a new one via process_factory
        process = overrides.pop("process", process_factory())

        values = {
            "process": process,
            "code": f"form-{index}",
            "name": f"Questionnaire {index}",
            "description": f"Questionnaire description {index}",
            "version": 1,
            "document": {
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
            "sort_order": index,
            "created_by": user,
        }
        values.update(overrides)
        return Questionnaire.objects.create(**values)

    return _create


@pytest.fixture
def questionnaire(db, process, user):
    """Create a single questionnaire for tests that need exactly one."""
    return Questionnaire.objects.create(
        process=process,
        code="new-application",
        name="New application",
        description="Create a new application",
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
def application_factory(db, user, questionnaire_factory):
    """Return a factory that creates application rows with configurable ownership and status."""

    def _create(**overrides):
        values = {
            "owner": overrides.pop("owner", user),
            "questionnaire": questionnaire_factory(),
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


@pytest.fixture
def application(db, user, questionnaire):
    """Create a single draft application for tests that need exactly one."""
    return Application.objects.create(
        owner=user,
        questionnaire=questionnaire,
        document={
            "schema_version": "2025.07-1",
            "active_step": 0,
            "steps": [{"is_valid": None, "answers": {}}],
        },
    )