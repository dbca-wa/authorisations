"""Security-focused API tests for non-disclosure semantics on foreign records."""

import uuid

import pytest
from rest_framework import status

from applications.models import ApplicationStatus


pytestmark = [pytest.mark.api, pytest.mark.security]


def _valid_document_payload():
    """Return a minimal valid document payload used for PUT mutation attempts."""
    return {
        "schema_version": "2025.07-1",
        "active_step": 0,
        "steps": [{"is_valid": True, "answers": {"0-0": "answer"}}],
    }


@pytest.mark.django_db
def test_application_put_returns_404_for_non_owner(
    api_client,
    user,
    other_user,
    application_factory,
):
    """Hide foreign applications by returning 404 on owner-forbidden PUT writes."""
    foreign_application = application_factory(owner=other_user, status=ApplicationStatus.DRAFT)

    api_client.force_authenticate(user=user)
    response = api_client.put(
        f"/api/applications/{foreign_application.key}",
        {"document": _valid_document_payload()},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_application_patch_returns_404_for_non_owner(
    api_client,
    user,
    other_user,
    application_factory,
):
    """Hide foreign applications by returning 404 on owner-forbidden PATCH writes."""
    foreign_application = application_factory(owner=other_user, status=ApplicationStatus.DRAFT)

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/applications/{foreign_application.key}",
        {"status": ApplicationStatus.SUBMITTED, "turnstile_token": "token"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_attachment_retrieve_returns_404_for_non_owner(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Hide foreign attachments by returning 404 on detail read attempts."""
    foreign_attachment = attachment_factory(application=application_factory(owner=other_user))

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/attachments/{foreign_attachment.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_attachment_patch_returns_404_for_non_owner(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Hide foreign attachments by returning 404 on detail write attempts."""
    foreign_attachment = attachment_factory(application=application_factory(owner=other_user))

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/attachments/{foreign_attachment.key}",
        {"name": "Should-not-rename.pdf"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_attachment_delete_returns_404_for_non_owner(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Hide foreign attachments by returning 404 on delete attempts."""
    foreign_attachment = attachment_factory(application=application_factory(owner=other_user))

    api_client.force_authenticate(user=user)
    response = api_client.delete(f"/api/attachments/{foreign_attachment.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_attachment_list_filter_does_not_disclose_foreign_or_unknown_application_keys(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Return identical empty results for foreign and unknown keys to reduce existence disclosure."""
    foreign_application = application_factory(owner=other_user)
    attachment_factory(application=foreign_application)

    unknown_key = uuid.uuid4()

    api_client.force_authenticate(user=user)
    foreign_response = api_client.get(
        "/api/attachments",
        {"application_key": str(foreign_application.key)},
    )
    unknown_response = api_client.get(
        "/api/attachments",
        {"application_key": str(unknown_key)},
    )

    assert foreign_response.status_code == status.HTTP_200_OK
    assert unknown_response.status_code == status.HTTP_200_OK
    assert foreign_response.data == []
    assert unknown_response.data == []
