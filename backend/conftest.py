import pytest
from rest_framework.test import APIClient

from applications.models import Application
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
def process(db):
    """Create a stable authorisation process fixture for questionnaire and application tests."""
    return AuthorisationProcess.objects.create(
        slug="s40",
        name="Section 40",
        description="Section 40 authorisation process",
        sort_order=1,
    )


@pytest.fixture
def questionnaire(db, process, user):
    """Create the latest questionnaire fixture used by backend application tests."""
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
def application(db, user, questionnaire):
    """Create a draft application that matches the canonical questionnaire fixture."""
    return Application.objects.create(
        owner=user,
        questionnaire=questionnaire,
        document={
            "schema_version": "2025.07-1",
            "active_step": 0,
            "steps": [{"is_valid": None, "answers": {}}],
        },
    )