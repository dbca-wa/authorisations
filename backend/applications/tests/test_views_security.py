"""Security tests for non-API Django views under /a/* and /d/* routes."""

from io import BytesIO

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from applications.models import Application, ApplicationAttachment

pytestmark = [pytest.mark.security, pytest.mark.integration, pytest.mark.django_db]


def _create_attachment(application: Application, filename: str = "evidence.pdf") -> ApplicationAttachment:
    """Create an attachment row linked to an application for download view tests."""
    return ApplicationAttachment.objects.create(
        application=application,
        question="0.0-0",
        name=filename,
        file=SimpleUploadedFile(
            name=filename,
            content=(b"%PDF-1.4\n" + b"0" * 64),
            content_type="application/pdf",
        ),
    )


def _enable_reviewer_access(application: Application, reviewer_group: Group) -> None:
    """Grant reviewer-group read access to the application's process."""
    application.questionnaire.process.reviewer_groups.add(reviewer_group)


def test_resume_application_returns_404_for_unauthenticated_user(client, application_factory):
    """Return 404 for anonymous users to avoid disclosing application existence via /a/*."""
    application = application_factory()
    response = client.get(reverse("resume-application", kwargs={"key": application.key}))

    assert response.status_code == 404


def test_resume_application_returns_404_for_non_owner_user(client, user, other_user, application_factory):
    """Return 404 when a non-owner tries to open another user's editable form URL."""
    application = application_factory(owner=other_user)

    client.force_login(user)
    response = client.get(reverse("resume-application", kwargs={"key": application.key}))

    assert response.status_code == 404


def test_resume_application_returns_200_for_owner(client, user, application_factory):
    """Allow owners to resume their own application through the /a/* form URL."""
    application = application_factory(owner=user)

    client.force_login(user)
    response = client.get(reverse("resume-application", kwargs={"key": application.key}))

    assert response.status_code == 200


def test_resume_application_returns_404_for_reviewer_non_owner(
    client,
    user,
    other_user,
    application_factory,
):
    """Keep /a/* owner-only even when reviewer read access exists for the process."""
    application = application_factory(owner=other_user)

    reviewer_group = Group.objects.create(name="reviewers-resume")
    user.groups.add(reviewer_group)
    _enable_reviewer_access(application, reviewer_group)

    client.force_login(user)
    response = client.get(reverse("resume-application", kwargs={"key": application.key}))

    assert response.status_code == 404


def test_resume_application_returns_404_for_unknown_key(client, user):
    """Return 404 for unknown application keys so callers cannot infer stale or mistyped records."""
    client.force_login(user)
    response = client.get(
        reverse(
            "resume-application",
            kwargs={"key": "00000000-0000-0000-0000-000000000000"},
        )
    )

    assert response.status_code == 404


def test_download_application_returns_404_for_unauthorised_user(client, user, other_user, application_factory):
    """Return 404 for foreign users on /d/<appKey> to prevent existence disclosure."""
    application = application_factory(owner=other_user)

    client.force_login(user)
    response = client.get(reverse("download-application", kwargs={"appKey": application.key}))

    assert response.status_code == 404


def test_download_application_returns_200_for_owner(client, user, application_factory, monkeypatch):
    """Allow owners to download their own generated application PDF."""
    application = application_factory(owner=user)

    monkeypatch.setattr(
        Application,
        "generate_pdf",
        lambda self, request=None: BytesIO(b"pdf-bytes"),
    )

    client.force_login(user)
    response = client.get(reverse("download-application", kwargs={"appKey": application.key}))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


def test_download_application_returns_200_for_reviewer_with_process_access(client, user, application_factory, monkeypatch):
    """Allow reviewer-group users to read/download applications they are authorised to review."""
    application = application_factory()
    
    reviewer_group = Group.objects.create(name="reviewers-download")
    user.groups.add(reviewer_group)
    _enable_reviewer_access(application, reviewer_group)

    monkeypatch.setattr(
        Application,
        "generate_pdf",
        lambda self, request=None: BytesIO(b"pdf-bytes"),
    )

    client.force_login(user)
    response = client.get(reverse("download-application", kwargs={"appKey": application.key}))

    assert response.status_code == 200


def test_download_application_returns_404_for_unknown_key(client, user):
    """Return 404 when download is requested for an application key that does not exist."""
    client.force_login(user)
    response = client.get(
        reverse(
            "download-application",
            kwargs={"appKey": "00000000-0000-0000-0000-000000000000"},
        )
    )

    assert response.status_code == 404


def test_download_attachment_returns_404_for_unauthorised_user(client, user, other_user, application_factory):
    """Return 404 for foreign users on /d/<appKey>/<attachmentKey> endpoints."""
    application = application_factory(owner=other_user)
    attachment = _create_attachment(application)

    client.force_login(user)
    response = client.get(
        reverse(
            "download-attachment",
            kwargs={"appKey": application.key, "attachmentKey": attachment.key},
        )
    )

    assert response.status_code == 404


def test_download_attachment_returns_200_for_owner(client, user, application_factory):
    """Allow owners to download their own non-deleted attachment files."""
    application = application_factory(owner=user)
    attachment = _create_attachment(application)

    client.force_login(user)
    response = client.get(
        reverse(
            "download-attachment",
            kwargs={"appKey": application.key, "attachmentKey": attachment.key},
        )
    )

    assert response.status_code == 200


def test_download_attachment_returns_200_for_reviewer_with_process_access(client, user, application_factory):
    """Allow reviewer-group users to read/download attachments for reviewable processes."""
    application = application_factory()
    
    reviewer_group = Group.objects.create(name="reviewers-attachment")
    user.groups.add(reviewer_group)
    _enable_reviewer_access(application, reviewer_group)
    attachment = _create_attachment(application)

    client.force_login(user)
    response = client.get(
        reverse(
            "download-attachment",
            kwargs={"appKey": application.key, "attachmentKey": attachment.key},
        )
    )

    assert response.status_code == 200


def test_download_attachment_returns_404_when_attachment_is_soft_deleted(client, user, application_factory):
    """Hide soft-deleted attachments from download endpoints with 404 responses."""
    application = application_factory(owner=user)
    attachment = _create_attachment(application)
    attachment.soft_delete()

    client.force_login(user)
    response = client.get(
        reverse(
            "download-attachment",
            kwargs={"appKey": application.key, "attachmentKey": attachment.key},
        )
    )

    assert response.status_code == 404
