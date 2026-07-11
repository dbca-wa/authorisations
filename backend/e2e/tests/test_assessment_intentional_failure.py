"""E2E debug test: intentionally fail on Assessment page to validate artefact capture."""

import pytest


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_intentional_failure_for_debug_artifacts(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Intentionally fail after loading Assessment page."""

    reviewer = e2e_users["reviewer"]
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    page.goto("/assessment")
    page.wait_for_load_state("networkidle")

    # Intentional failure to validate debug artefacts (screenshot, HTML, JSON, video).
    assert page.locator('text=INTENTIONAL_E2E_FAILURE_SENTINEL').count() == 1
