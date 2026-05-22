"""Shared fixtures for API endpoint test modules.

This package-local conftest keeps API-focused factories close to endpoint
behaviour tests while reusing core fixtures from backend/conftest.py.
"""

from itertools import count

import pytest
from django.contrib.auth.models import Group

from applications.models import Application, ApplicationAttachment, ApplicationStatus
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire


@pytest.fixture
def assessor_group(db):
    """Create the canonical assessor group used in review authorisation tests."""
    return Group.objects.create(name="assessors")


@pytest.fixture
def assessor_user(db, assessor_group):
    """Create an authenticated assessor user linked to the assessor group."""
    from users.models import User

    user = User.objects.create_user(username="assessor", password="testpass123")
    user.groups.add(assessor_group)
    return user


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
def questionnaire_factory(db, process_factory, user):
    """Return a factory that creates questionnaires for list/retrieve and versioning tests."""
    sequence = count(1)

    def _create(**overrides):
        index = next(sequence)
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
def application_factory(db, user, questionnaire_factory):
    """Return a factory that creates application rows with configurable ownership and status."""

    def _create(**overrides):
        values = {
            "owner": user,
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
def attachment_factory(db, application_factory):
    """Return a factory that creates attachment records bound to application/question pairs."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    sequence = count(1)

    def _create(**overrides):
        index = next(sequence)
        values = {
            "application": application_factory(),
            "question": "0.0-0",
            "name": f"Attachment {index}.pdf",
            "file": SimpleUploadedFile(
                name=f"attachment-{index}.pdf",
                content=(b"%PDF-1.4\n" + b"0" * 64),
                content_type="application/pdf",
            ),
            "is_deleted": False,
        }
        values.update(overrides)
        return ApplicationAttachment.objects.create(**values)

    return _create
