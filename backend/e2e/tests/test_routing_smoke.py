"""Request-level routing smoke tests against Django live_server."""

import pytest


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_root_redirects_to_my_applications(playwright, live_server):
    """Verify the local test server redirects `/` to `/my-applications` with HTTP 302."""
    request_context = playwright.request.new_context(base_url=live_server.url)
    try:
        response = request_context.get("/", max_redirects=0)
        status = response.status
        location = response.headers.get("location")
    finally:
        request_context.dispose()

    assert status == 302
    assert location == "/my-applications"


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_authenticated_shell_routes_render_spa_container(
    authenticated_request_context_factory,
    e2e_users,
):
    """Ensure authenticated users can load SPA shell routes used by core flows."""
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        my_apps = request_context.get("/my-applications")
        new_application = request_context.get("/new-application")
        my_apps_status = my_apps.status
        my_apps_body = my_apps.text()
        new_application_status = new_application.status
        new_application_body = new_application.text()
    finally:
        request_context.dispose()

    assert my_apps_status == 200
    assert '<div id="root"></div>' in my_apps_body
    assert new_application_status == 200
    assert '<div id="root"></div>' in new_application_body