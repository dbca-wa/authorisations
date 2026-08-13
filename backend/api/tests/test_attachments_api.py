"""API tests for application attachment CRUD and access boundaries."""

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

pytestmark = [pytest.mark.api]


def _pdf_upload(name="upload.pdf"):
    """Build a minimal PDF payload accepted by the attachment file validator."""
    return SimpleUploadedFile(
        name=name,
        content=(b"%PDF-1.4\n" + b"0" * 64),
        content_type="application/pdf",
    )


@pytest.mark.django_db
@pytest.mark.security
def test_attachments_list_requires_authentication(api_client):
    """Require authentication for attachment listing to avoid exposing file metadata."""
    response = api_client.get("/api/attachments")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.security
def test_attachments_list_returns_only_owner_non_deleted_records(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Return only owner attachments that are not soft-deleted."""
    own_attachment = attachment_factory(application=application_factory(owner=user))
    attachment_factory(
        application=application_factory(owner=user),
        is_deleted=True,
    )
    attachment_factory(application=application_factory(owner=other_user))

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/attachments")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(own_attachment.key)


@pytest.mark.django_db
def test_attachments_list_returns_reviewable_application_attachments_for_reviewer(
    api_client,
    user,
    other_user,
    attachment_factory,
    application_factory,
):
    """Allow reviewers to inspect attachments for applications in processes they can assess."""
    reviewer_group = Group.objects.create(name="reviewers-attachments")
    user.groups.add(reviewer_group)

    reviewable_application = application_factory(owner=other_user)
    reviewable_application.questionnaire.process.reviewer_groups.add(reviewer_group)
    attachment = attachment_factory(application=reviewable_application)

    api_client.force_authenticate(user=user)
    response = api_client.get(
        "/api/attachments",
        {"application_key": str(reviewable_application.key)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [item["key"] for item in response.data] == [str(attachment.key)]


@pytest.mark.django_db
@pytest.mark.security
def test_attachments_filter_rejects_invalid_application_uuid(api_client, user):
    """Reject malformed UUID filters to harden attachment query parameters."""
    api_client.force_authenticate(user=user)

    response = api_client.get("/api/attachments", {"application_key": "not-a-uuid"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "badly formed hexadecimal UUID string" in str(response.data)


@pytest.mark.django_db
def test_attachments_filter_by_application_key_returns_expected_subset(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Filter attachments by application key to support question-level file loading."""
    target_application = application_factory(owner=user)
    other_application = application_factory(owner=user)
    target_attachment = attachment_factory(application=target_application)
    attachment_factory(application=other_application)

    api_client.force_authenticate(user=user)
    response = api_client.get(
        "/api/attachments",
        {"application_key": str(target_application.key)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(target_attachment.key)


@pytest.mark.django_db
@pytest.mark.security
def test_attachment_create_rejects_application_not_owned_by_user(
    api_client,
    user,
    other_user,
    application_factory,
):
    """Block attachment creation when the referenced application belongs to another user."""
    foreign_application = application_factory(owner=other_user)

    api_client.force_authenticate(user=user)
    response = api_client.post(
        "/api/attachments",
        {
            "application_key": str(foreign_application.key),
            "question": "0.0-0",
            "name": "Evidence.pdf",
            "file": _pdf_upload("evidence.pdf"),
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "application_key" in response.data


@pytest.mark.django_db
def test_attachment_delete_soft_deletes_and_hides_from_list(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Soft-delete attachments and remove them from list responses."""
    attachment = attachment_factory(application=application_factory(owner=user))

    api_client.force_authenticate(user=user)
    delete_response = api_client.delete(f"/api/attachments/{attachment.key}")

    attachment.refresh_from_db()
    list_response = api_client.get("/api/attachments")

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert attachment.is_deleted is True
    assert all(item["key"] != str(attachment.key) for item in list_response.data)


@pytest.mark.django_db
def test_attachment_patch_allows_rename_only(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Allow renaming an attachment while preserving all immutable file metadata."""
    attachment = attachment_factory(application=application_factory(owner=user), name="Original.pdf")

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/attachments/{attachment.key}",
        {"name": "Renamed.pdf"},
        format="json",
    )

    attachment.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert attachment.name == "Renamed.pdf"


@pytest.mark.django_db
def test_attachment_patch_rejects_file_mutation(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Reject PATCH requests that attempt to mutate file content instead of name."""
    attachment = attachment_factory(application=application_factory(owner=user))

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/attachments/{attachment.key}",
        {
            "file": _pdf_upload("replacement.pdf"),
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data


@pytest.mark.django_db
def test_attachment_create_captures_file_size(
    api_client,
    user,
    application_factory,
):
    """Verify file size is automatically captured during attachment creation."""
    application = application_factory(owner=user)
    pdf_file = _pdf_upload("test.pdf")
    expected_size = pdf_file.size

    api_client.force_authenticate(user=user)
    response = api_client.post(
        "/api/attachments",
        {
            "application_key": str(application.key),
            "question": "0.0-0",
            "name": "test.pdf",
            "file": pdf_file,
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["size"] == expected_size
    assert response.data["size"] > 0


@pytest.mark.django_db
def test_attachment_list_includes_size_field(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Verify attachment list responses include size field for each attachment."""
    attachment = attachment_factory(application=application_factory(owner=user), size=1024)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/attachments")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["size"] == 1024


@pytest.mark.django_db
def test_attachment_size_is_readonly_on_patch(
    api_client,
    user,
    attachment_factory,
    application_factory,
):
    """Verify size field cannot be mutated via PATCH requests."""
    attachment = attachment_factory(application=application_factory(owner=user), size=2048)

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/attachments/{attachment.key}",
        {
            "name": "renamed.pdf",
            "size": 9999,  # Attempt to mutate size
        },
        format="json",
    )

    attachment.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert attachment.size == 2048  # Size should remain unchanged
    assert attachment.name == "renamed.pdf"  # Name should be updated
