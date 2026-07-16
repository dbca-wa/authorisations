"""Request-level E2E tests for API contract behaviours."""

import pytest
from django.conf import settings


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_session_cookie_is_not_overridden_by_parent_domain_cookie(
    playwright,
    live_server,
    client,
    e2e_users,
):
    """Keep the authenticated session stable when a parent-domain cookie is also present.

    Firefox may serialise cookies with the host-scoped cookie first and the
    parent-domain cookie second. Authorisations must continue to use its own
    host-scoped session cookie and ignore the unrelated parent-domain value.
    """
    client.force_login(e2e_users["applicant"])
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value

    request_context = playwright.request.new_context(
        base_url=live_server.url,
        extra_http_headers={
            "Cookie": f"{settings.SESSION_COOKIE_NAME}={session_cookie}; sessionid=parent-domain-session",
        },
    )

    try:
        response = request_context.get("/api/applications")
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 200
    assert len(payload) == 1
    assert payload[0]["owner_email"] == "e2e-applicant@example.com"


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
    # Verify process_name is included in the response
    assert all("process_name" in item for item in payload)
    assert all(item["process_name"] for item in payload)  # Ensure it's not empty


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
    assert payload[0]["owner_email"] == "e2e-applicant@example.com"
    assert payload[0]["owner_fullname"] == "E2E Applicant"
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