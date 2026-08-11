"""View tests for file handling edge cases (non-security).

These tests focus on storage/backend behaviour such as missing blobs and
ensure views return an appropriate 404 response instead of raising.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from applications.models import ApplicationAttachment

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def _create_attachment(application, filename: str = "evidence.pdf") -> ApplicationAttachment:
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


def test_download_attachment_returns_404_when_file_missing_in_storage(
    client, user, application_factory, monkeypatch
):
    """Return 404 when the DB record exists but the underlying file is missing.

    This reproduces scenarios where the database was copied from another
    environment (UAT/production) but the storage bucket does not contain the
    referenced blob. The view should return a 404 rather than raising an
    exception.
    """
    application = application_factory(owner=user)
    attachment = _create_attachment(application)

    # Simulate Azure's ResourceNotFoundError when opening the file.
    from azure.core.exceptions import ResourceNotFoundError

    def _raise_missing(*args, **kwargs):
        raise ResourceNotFoundError("The specified blob does not exist.")

    # Patch the storage backend's open method so FieldFile.open triggers
    # the ResourceNotFoundError when it attempts to open the underlying blob.
    monkeypatch.setattr(attachment.file.storage, "open", lambda name, mode="rb": _raise_missing())

    client.force_login(user)
    response = client.get(
        reverse(
            "download-attachment",
            kwargs={"appKey": application.key, "attachmentKey": attachment.key},
        )
    )

    assert response.status_code == 404
