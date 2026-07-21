"""E2E: editor and submission flow (form fill → review → submit → download).

This test focuses on the unique workflow aspects: form filling in the editor,
review page interaction, application submission, and PDF download verification.

Dialog/consent/confirmation flows are covered separately in test_new_application_page.py.
"""

from urllib.parse import urlparse
import pytest


@pytest.mark.skip
@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_form_fill_submit_and_download(
    authenticated_browser_context_factory,
    authenticated_request_context_factory,
    e2e_users,
    mock_turnstile_script,
):
    """Test editor form completion, review, submission, and PDF download availability."""
    applicant = e2e_users["applicant"]

    # Create an in-progress application via API (bypassing dialog flow tested elsewhere)
    auth_context = authenticated_request_context_factory(applicant)
    from questionnaires.models import Questionnaire
    import json
    
    questionnaire = Questionnaire.objects.select_related("process").get(
        process__slug="aec", code="new-application", version=1
    )
    request_context = auth_context["context"]
    
    try:
        response = request_context.post(
            "/api/applications",
            data=json.dumps({
                "process_slug": questionnaire.process.slug,
                "questionnaire_id": questionnaire.id,
                "questionnaire_code": questionnaire.code,
                "questionnaire_version": questionnaire.version,
                "privacy_consent_agreed": True,
                "turnstile_token": "e2e-turnstile-token",
            }),
            headers={
                str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
                "Content-Type": "application/json",
            },
        )
        app_key = response.json()["key"]
    finally:
        request_context.dispose()

    # Open editor in authenticated context with Turnstile mock
    context = authenticated_browser_context_factory(applicant)
    editor_page = context.new_page()
    mock_turnstile_script(editor_page)

    # Navigate to editor and fill form
    editor_page.goto(f"/a/{app_key}")
    editor_page.wait_for_selector('div#root')
    
    # Fill the simple form (seed questionnaires use a single text field)
    title_input = editor_page.get_by_label("Project title")
    title_input.fill("E2E Project Title")

    # Continue to review page (triggers save)
    editor_page.get_by_role("button", name="Continue").click()

    # On review page, accept consent and submit
    mock_turnstile_script(editor_page)
    editor_page.wait_for_selector('input[type="checkbox"]:not([disabled])', timeout=5000)
    editor_page.locator('input[type="checkbox"]').click()
    editor_page.get_by_role("button", name="Submit Application").click()

    # Verify submission succeeded (redirect or URL change)
    editor_page.wait_for_url(lambda url: "a/" not in url, timeout=5000)

    # Verify PDF is available for download
    my_apps_page = context.new_page()
    my_apps_page.goto("/my-applications")
    download_selector = f'a[aria-label="Download application PDF"][href="/d/{app_key}"]'
    my_apps_page.wait_for_selector(download_selector, timeout=5000)

    # Verify download endpoint returns PDF
    req_auth = authenticated_request_context_factory(applicant)
    req_ctx = req_auth["context"]
    try:
        resp = req_ctx.get(f"/d/{app_key}")
        assert resp.status == 200
        assert resp.body().startswith(b"%PDF")
    finally:
        req_ctx.dispose()

    # Clean up
    editor_page.close()
    my_apps_page.close()
    context.close()
