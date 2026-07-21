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
    # Latest versions: s40 new-application (v2), s40 renewal (v1), aec new-application (v1), s45 new-application (v1)
    assert len(payload) == 4
    assert identifiers == {("s40", "new-application"), ("s40", "renewal"), ("aec", "new-application"), ("s45", "new-application")}
    assert all(item["version"] >= 1 for item in payload)
    assert not any(item["process_slug"] == "s40" and item["code"] == "new-application" and item["version"] == 1 for item in payload)
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


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_questionnaire_list_orders_by_process_sort_order_then_questionnaire_sort_order(
    authenticated_request_context_factory,
    e2e_users,
):
    """Verify real API response orders questionnaires by process sort_order, then questionnaire sort_order.
    
    This E2E test uses seed data where:
    - Process s40 (sort_order=1) has questionnaires: new-application (sort_order=1), renewal (sort_order=2)
    - Process aec (sort_order=2) has questionnaire: new-application (sort_order=1)
    - Process s45 (sort_order=3) has questionnaire: new-application (sort_order=1)
    
    Verifies the API returns them in correct sorted order.
    """
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get("/api/questionnaires")
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 200
    
    # Get codes and process slugs in order to verify sorting
    results_in_order = [(item["process_slug"], item["code"]) for item in payload]
    
    # Verify order: 
    # - s40 (sort_order=1) comes first with new-application before renewal
    # - aec (sort_order=2) comes second
    # - s45 (sort_order=3) comes third
    assert results_in_order == [
        ("s40", "new-application"),  # s40, sort_order=1
        ("s40", "renewal"),          # s40, sort_order=2
        ("aec", "new-application"),  # aec, sort_order=1
        ("s45", "new-application"),  # s45, sort_order=1
    ]


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_processes_list_orders_by_sort_order(
    authenticated_request_context_factory,
    e2e_users,
):
    """Verify real API response orders processes by sort_order ascending.
    
    This E2E test uses seed data with processes created in random order:
    - s40 (sort_order=1)
    - aec (sort_order=2)  
    - s45 (sort_order=3)
    
    Verifies the API returns them sorted by sort_order, not by slug or name.
    """
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get("/api/processes")
        status = response.status
        payload = response.json()
    finally:
        request_context.dispose()

    assert status == 200
    
    # Verify slugs are in sort_order order
    slugs_in_order = [item["slug"] for item in payload]
    assert slugs_in_order == ["s40", "aec", "s45"]
    
    # Verify sort_order values are in ascending order
    sort_orders = [item["sort_order"] for item in payload]
    assert sort_orders == [1, 2, 3]