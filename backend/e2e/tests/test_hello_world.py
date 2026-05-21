"""Minimal Playwright E2E redirect test against Django live_server."""

import pytest


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_root_redirects_to_my_applications(playwright, live_server):
    """Verify the local test server redirects `/` to `/my-applications` with HTTP 302."""
    base_url = live_server.url

    request_context = playwright.request.new_context(base_url=base_url)
    try:
        response = request_context.get("/", max_redirects=0)
    finally:
        request_context.dispose()

    assert response.status == 302
    assert response.headers.get("location") == "/my-applications"
