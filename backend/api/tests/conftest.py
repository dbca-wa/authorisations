"""Shared fixtures for API endpoint test modules.

This module defines API-specific fixtures. Common factories (questionnaire_factory,
application_factory, process_factory) are inherited from backend/conftest.py.
"""

import pytest
from applications.models import ApplicationAttachment
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from itertools import count


@pytest.fixture
def reviewer_group(db):
    """Create the canonical reviewer group used in review authorisation tests."""
    return Group.objects.create(name="reviewers")


@pytest.fixture
def reviewer_user(db, reviewer_group):
    """Create an authenticated reviewer user linked to the reviewer group."""
    from users.models import User

    user = User.objects.create_user(username="reviewer", password="testpass123")
    user.groups.add(reviewer_group)
    return user


@pytest.fixture
def attachment_factory(db, application_factory):
    """Return a factory that creates attachment records bound to application/question pairs."""
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
