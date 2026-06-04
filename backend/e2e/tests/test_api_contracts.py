"""Request-level E2E tests for API contract behaviours."""

import pytest


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_questionnaire_list_returns_latest_versions_only(
    authenticated_request_context_factory,
    e2e_users,
):
    """Ensure API list emits only the latest questionnaire per process/code pair."""
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get("/api/questionnaires")
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    identifiers = {(item["process_slug"], item["code"]) for item in payload}

    assert status == 200
    assert len(payload) == 2
    assert identifiers == {("s40", "new-application"), ("aec", "new-application")}
    assert all(item["version"] >= 1 for item in payload)
    assert not any(item["process_slug"] == "s40" and item["version"] == 1 for item in payload)


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_applications_list_is_owner_scoped(
    authenticated_request_context_factory,
    e2e_users,
):
    """Ensure application list endpoint only returns records for the authenticated owner."""
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get("/api/applications")
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 200
    assert len(payload) == 1
    assert payload[0]["owner"] == "e2e-applicant"
    assert payload[0]["status"] == "DRAFT"


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_attachment_filter_rejects_invalid_application_key(
    authenticated_request_context_factory,
    e2e_users,
):
    """Return 400 for malformed application_key query parameter values."""
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get("/api/attachments?application_key=not-a-uuid")
        status = response.status
    finally:
        request_context.dispose()

    assert status == 400