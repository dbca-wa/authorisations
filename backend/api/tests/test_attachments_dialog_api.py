"""Additional API tests for attachments list behaviour used by the UI dialog."""

import pytest
from django.contrib.auth.models import Group
from rest_framework import status

from applications.models import ApplicationAttachment


@pytest.mark.django_db
def test_get_attachments_for_application_returns_empty_for_reviewer(
    api_client, user, other_user, application_factory
):
    """Reviewer may query attachments for an application that currently has none."""
    # Arrange: ensure reviewer group and process mapping exists
    reviewer_group = Group.objects.create(name="reviewers-attachments-dialog")
    user.groups.add(reviewer_group)

    # Application owned by other_user in a reviewable process (seed or factory should set process)
    application = application_factory(owner=other_user)
    # Ensure process has the reviewer group
    application.questionnaire.process.reviewer_groups.add(reviewer_group)

    api_client.force_authenticate(user=user)

    # Act
    response = api_client.get("/api/attachments", {"application_key": str(application.key)})

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_get_attachments_for_application_returns_attachments_for_reviewer(
    api_client, user, other_user, attachment_factory, application_factory
):
    """Reviewer may query and receive attachment records for a reviewable application."""
    reviewer_group = Group.objects.create(name="reviewers-attachments-dialog-2")
    user.groups.add(reviewer_group)

    reviewable_application = application_factory(owner=other_user)
    reviewable_application.questionnaire.process.reviewer_groups.add(reviewer_group)

    attachment = attachment_factory(application=reviewable_application, name="evidence-1.txt")
    api_client.force_authenticate(user=user)
    # Sanity check: attachment should exist in DB for the given application
    assert ApplicationAttachment.objects.filter(application=reviewable_application, key=attachment.key).exists()

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/attachments", {"application_key": str(reviewable_application.key)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == "evidence-1.txt"
