"""API tests for applicant-facing application endpoints."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

import applications.serialisers as application_serialisers
from applications.models import ApplicationStatus


pytestmark = [pytest.mark.api]


def _build_create_payload(questionnaire):
    """Build the canonical application creation payload from questionnaire identity fields."""
    return {
        "process_slug": questionnaire.process.slug,
        "questionnaire_id": questionnaire.id,
        "questionnaire_code": questionnaire.code,
        "questionnaire_version": questionnaire.version,
        "privacy_consent_agreed": True,
        "turnstile_token": "test-token",
    }


@pytest.mark.django_db
@pytest.mark.security
def test_applications_list_requires_authentication(api_client):
    """Require authentication for application listing so applicant data never leaks anonymously."""
    response = api_client.get("/api/applications")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.security
def test_applications_list_is_owner_scoped(api_client, user, other_user, application_factory):
    """Return only the authenticated owner's records in application list responses."""
    own_application = application_factory(owner=user)
    application_factory(owner=other_user)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/applications")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(own_application.key)


@pytest.mark.django_db
@pytest.mark.security
def test_applications_retrieve_is_owner_scoped(api_client, user, other_user, application_factory):
    """Deny direct key-based retrieval of another user's application."""
    foreign_application = application_factory(owner=other_user)

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/applications/{foreign_application.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_applications_list_omits_document_but_retrieve_includes_it(
    api_client,
    user,
    application_factory,
):
    """Keep list payloads small while preserving full detail data on retrieve."""
    application = application_factory(owner=user)

    api_client.force_authenticate(user=user)
    list_response = api_client.get("/api/applications")
    retrieve_response = api_client.get(f"/api/applications/{application.key}")

    assert list_response.status_code == status.HTTP_200_OK
    assert "document" not in list_response.data[0]
    assert retrieve_response.status_code == status.HTTP_200_OK
    assert "document" in retrieve_response.data


@pytest.mark.django_db
def test_application_create_requires_privacy_consent(
    api_client,
    user,
    questionnaire,
    monkeypatch,
):
    """Reject creation unless privacy consent is explicitly acknowledged."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: True)
    payload = _build_create_payload(questionnaire)
    payload["privacy_consent_agreed"] = False

    api_client.force_authenticate(user=user)
    response = api_client.post("/api/applications", payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "privacy_consent_agreed" in response.data


@pytest.mark.django_db
def test_application_create_rejects_mismatched_questionnaire_identity(
    api_client,
    user,
    questionnaire,
    monkeypatch,
):
    """Enforce process/id/code/version identity integrity during application creation."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: True)
    payload = _build_create_payload(questionnaire)
    payload["questionnaire_code"] = "not-the-real-code"

    api_client.force_authenticate(user=user)
    response = api_client.post("/api/applications", payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Questionnaire with the provided process slug" in str(response.data)


@pytest.mark.django_db
@pytest.mark.security
def test_application_create_rejects_invalid_turnstile_token(
    api_client,
    user,
    questionnaire,
    monkeypatch,
):
    """Fail closed on create when Turnstile verification fails."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: False)
    payload = _build_create_payload(questionnaire)

    api_client.force_authenticate(user=user)
    response = api_client.post("/api/applications", payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "turnstile_token" in response.data


@pytest.mark.django_db
def test_application_patch_draft_to_submitted_sets_submitted_at(
    api_client,
    user,
    application_factory,
    monkeypatch,
):
    """Stamp submitted_at when draft transitions to submitted through PATCH."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: True)
    application = application_factory(owner=user, status=ApplicationStatus.DRAFT)

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/applications/{application.key}",
        {"status": ApplicationStatus.SUBMITTED, "turnstile_token": "patch-token"},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == ApplicationStatus.SUBMITTED
    assert application.submitted_at is not None


@pytest.mark.django_db
def test_application_patch_preserves_existing_submitted_at_timestamp(
    api_client,
    user,
    application_factory,
    monkeypatch,
):
    """Avoid overwriting submitted_at when a legacy draft record already has a timestamp."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: True)
    initial_submitted_at = timezone.now() - timedelta(days=1)
    application = application_factory(
        owner=user,
        status=ApplicationStatus.DRAFT,
        submitted_at=initial_submitted_at,
    )

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/applications/{application.key}",
        {"status": ApplicationStatus.SUBMITTED, "turnstile_token": "patch-token"},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.submitted_at == initial_submitted_at


@pytest.mark.django_db
def test_application_patch_rejects_invalid_status_transition(
    api_client,
    user,
    application_factory,
    monkeypatch,
):
    """Reject unsupported status transitions to protect application lifecycle rules."""
    monkeypatch.setattr(application_serialisers, "verify_turnstile_token", lambda *_args, **_kwargs: True)
    application = application_factory(owner=user, status=ApplicationStatus.DRAFT)

    api_client.force_authenticate(user=user)
    response = api_client.patch(
        f"/api/applications/{application.key}",
        {"status": ApplicationStatus.APPROVED, "turnstile_token": "patch-token"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid status transition" in str(response.data)


@pytest.mark.django_db
def test_application_put_rejects_document_update_when_not_draft(
    api_client,
    user,
    application_factory,
):
    """Disallow document edits after an application has left draft state."""
    application = application_factory(owner=user, status=ApplicationStatus.SUBMITTED)

    api_client.force_authenticate(user=user)
    response = api_client.put(
        f"/api/applications/{application.key}",
        {
            "document": {
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": True, "answers": {"0-0": "updated"}}],
            }
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot modify document" in str(response.data)


@pytest.mark.django_db
def test_application_put_rejects_document_with_schema_version_mismatch(
    api_client,
    user,
    application_factory,
):
    """Reject document updates when payload schema_version does not match questionnaire schema."""
    application = application_factory(owner=user, status=ApplicationStatus.DRAFT)

    api_client.force_authenticate(user=user)
    response = api_client.put(
        f"/api/applications/{application.key}",
        {
            "document": {
                "schema_version": "1900.01-1",
                "active_step": 0,
                "steps": [{"is_valid": True, "answers": {"0-0": "updated"}}],
            }
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Schema version mismatch" in str(response.data)
