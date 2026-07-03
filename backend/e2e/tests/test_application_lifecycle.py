"""Request-driven E2E tests for application lifecycle business flows."""

import json

from questionnaires.models import Questionnaire
import pytest


def _auth_json_headers(auth_context: dict[str, object]) -> dict[str, str]:
    """Build JSON request headers with CSRF from an authenticated E2E context."""
    return {
        str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
        "Content-Type": "application/json",
    }


def _build_create_payload(questionnaire: Questionnaire, privacy_consent_agreed: bool) -> dict[str, object]:
    """Build a valid application-create payload for a questionnaire identity."""
    return {
        "process_slug": questionnaire.process.slug,
        "questionnaire_id": questionnaire.id,
        "questionnaire_code": questionnaire.code,
        "questionnaire_version": questionnaire.version,
        "privacy_consent_agreed": privacy_consent_agreed,
        "turnstile_token": "e2e-turnstile-token",
    }


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_create_application_requires_privacy_consent(
    authenticated_request_context_factory,
    e2e_users,
):
    """Reject create requests when privacy consent is not explicitly acknowledged."""
    questionnaire = Questionnaire.objects.select_related("process").get(process__slug="aec", code="new-application", version=1)
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.post(
            "/api/applications",
            data=json.dumps(_build_create_payload(questionnaire, privacy_consent_agreed=False)),
            headers=_auth_json_headers(auth_context),
        )
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 400
    assert "privacy_consent_agreed" in payload


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_create_application_requires_turnstile_token(
    authenticated_request_context_factory,
    e2e_users,
):
    """Reject create requests that omit the verification token."""
    questionnaire = Questionnaire.objects.select_related("process").get(process__slug="aec", code="new-application", version=1)
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]
    payload = _build_create_payload(questionnaire, privacy_consent_agreed=True)
    payload.pop("turnstile_token")

    try:
        response = request_context.post(
            "/api/applications",
            data=json.dumps(payload),
            headers=_auth_json_headers(auth_context),
        )
        status = response.status
        response_payload = response.json()
    finally:
        request_context.dispose()

    assert status == 400
    assert "turnstile_token" in response_payload


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_create_application_with_valid_payload_succeeds(
    authenticated_request_context_factory,
    e2e_users,
):
    """Create a new draft application with valid questionnaire identity and consent."""
    questionnaire = Questionnaire.objects.select_related("process").get(process__slug="aec", code="new-application", version=1)
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.post(
            "/api/applications",
            data=json.dumps(_build_create_payload(questionnaire, privacy_consent_agreed=True)),
            headers=_auth_json_headers(auth_context),
        )
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 201
    assert payload["owner"] == "e2e-applicant"
    assert payload["process_slug"] == "aec"
    assert payload["status"] == "DRAFT"
    assert "internal_id" in payload
    assert payload["internal_id"]  # Ensure it's not empty


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_submit_transition_makes_application_read_only(
    authenticated_request_context_factory,
    e2e_users,
):
    """Allow draft submission and then reject document updates after submission."""
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        draft_response = request_context.get("/api/applications")
        draft_payload = draft_response.json()
        draft_key = draft_payload[0]["key"]

        submit_response = request_context.patch(
            f"/api/applications/{draft_key}",
            data=json.dumps({"status": "SUBMITTED", "turnstile_token": "e2e-turnstile-token"}),
            headers=_auth_json_headers(auth_context),
        )
        submit_status = submit_response.status
        submit_payload = submit_response.json()

        update_response = request_context.put(
            f"/api/applications/{draft_key}",
            data=json.dumps(
                {
                    "document": {
                        "schema_version": "2025.07-1",
                        "active_step": 0,
                        "steps": [{"is_valid": True, "answers": {"0-0": "Should fail after submit"}}],
                    }
                }
            ),
            headers=_auth_json_headers(auth_context),
        )
        update_status = update_response.status
        update_payload = update_response.json()
    finally:
        request_context.dispose()

    assert submit_status == 200
    assert submit_payload["status"] == "SUBMITTED"
    assert submit_payload["submitted_at"] is not None
    assert update_status == 400
    assert update_payload["document"] == ["Cannot modify document with status 'SUBMITTED'"]