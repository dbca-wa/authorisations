"""Request-driven E2E tests for application lifecycle business flows."""

import json

import pytest


def _auth_json_headers(auth_context: dict[str, object]) -> dict[str, str]:
    """Build JSON request headers with CSRF from an authenticated E2E context."""
    return {
        str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
        "Content-Type": "application/json",
    }






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