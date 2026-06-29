"""Unit tests for questionnaire admin change view access control."""

import pytest
from django.test import Client

from questionnaires.admin import QuestionnaireAdmin
from questionnaires.models import Questionnaire
from users.models import User


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


@pytest.fixture
def staff_user(db):
    """Create a staff user who can access the admin."""
    user = User.objects.create_user(username="staff", password="testpass123")
    user.is_staff = True
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def questionnaire_versions(db, process, user):
    """Create two versions of the same questionnaire (version 1 and version 2)."""
    v1 = Questionnaire.objects.create(
        process=process,
        code="test-qnaire",
        name="Test Questionnaire",
        description="Version 1",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    v2 = Questionnaire.objects.create(
        process=process,
        code="test-qnaire",
        name="Test Questionnaire",
        description="Version 2",
        version=2,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    return v1, v2


def test_change_view_allows_latest_version_access(
    db, staff_user, questionnaire_versions
):
    """Latest version should return 200 OK via admin change view."""
    v1, v2 = questionnaire_versions

    client = Client()
    client.force_login(staff_user)
    response = client.get(f"/admin/questionnaires/questionnaire/{v2.id}/change/")

    # Latest version should be accessible
    assert response.status_code == 200


def test_change_view_raises_404_for_old_version(db, staff_user, questionnaire_versions):
    """Older version should return 404 when accessed via admin change view."""
    v1, v2 = questionnaire_versions

    client = Client()
    client.force_login(staff_user)
    response = client.get(f"/admin/questionnaires/questionnaire/{v1.id}/change/")

    # Older version should be blocked
    assert response.status_code == 404


def test_is_latest_version_helper_identifies_latest(db, questionnaire_versions):
    """_is_latest_version helper should correctly identify latest version."""
    v1, v2 = questionnaire_versions

    admin = QuestionnaireAdmin(Questionnaire, admin_site=None)

    assert admin._is_latest_version(v2) is True
    assert admin._is_latest_version(v1) is False


def test_is_latest_version_with_single_version(db, process, user):
    """_is_latest_version should return True for only version."""
    qnaire = Questionnaire.objects.create(
        process=process,
        code="single-version",
        name="Single Version",
        description="Only version",
        version=1,
        document=_document(),
        sort_order=1,
        created_by=user,
    )

    admin = QuestionnaireAdmin(Questionnaire, admin_site=None)
    assert admin._is_latest_version(qnaire) is True
