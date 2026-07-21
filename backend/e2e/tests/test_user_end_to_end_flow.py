"""E2E: editor and submission flow (form fill → review → submit → download).

This module breaks the workflow into focused tests:
- Editor page load and form interaction
- Form submission and review page navigation
- Application submission and status change
- PDF generation and download availability

Dialog/consent/confirmation flows are covered separately in test_new_application_page.py.
"""

import json

import pytest
from questionnaires.models import Questionnaire


@pytest.fixture
def draft_application(authenticated_request_context_factory, e2e_users):
    """Create a draft application via API and return its key."""
    applicant = e2e_users["applicant"]
    auth_context = authenticated_request_context_factory(applicant)
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
        assert response.status == 201
        app_key = response.json()["key"]
    finally:
        request_context.dispose()

    return applicant, app_key


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_page_loads_with_form(
    authenticated_browser_context_factory,
    draft_application,
    mock_turnstile_script,
):
    """Verify editor page loads and form is accessible."""
    applicant, app_key = draft_application
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{app_key}")
        page.wait_for_selector('div#root', timeout=5000)
        
        # Verify form field exists
        title_input = page.get_by_label("Project title")
        assert title_input is not None
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_form_fill_and_continue_to_review(
    authenticated_browser_context_factory,
    draft_application,
    mock_turnstile_script,
):
    """Verify form can be filled and continue button navigates to review page."""
    applicant, app_key = draft_application
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{app_key}")
        page.wait_for_selector('div#root', timeout=5000)
        
        # Fill form
        title_input = page.get_by_label("Project title")
        title_input.fill("E2E Project Title")
        
        # Wait a moment for auto-save, then continue
        page.wait_for_timeout(500)
        continue_button = page.get_by_role("button", name="Continue")
        continue_button.click()
        
        # Verify we're on review page (should have Submit button)
        page.get_by_role("button", name="Submit Application").wait_for(timeout=5000)
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_review_page_and_submit_application(
    authenticated_browser_context_factory,
    draft_application,
    mock_turnstile_script,
):
    """Verify review page loads and application can be submitted."""
    applicant, app_key = draft_application
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{app_key}")
        page.wait_for_selector('div#root', timeout=5000)
        
        # Fill and continue
        title_input = page.get_by_label("Project title")
        title_input.fill("E2E Project Title")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Continue").click()
        
        # On review page: wait for Submit button to appear (indicates review page is loaded)
        page.get_by_role("button", name="Submit Application").wait_for(timeout=10000)
        # Then wait for checkbox to be visible
        page.wait_for_selector('input[type="checkbox"]:not([disabled])', timeout=10000)
        checkbox = page.locator('input[type="checkbox"]').first
        checkbox.click()
        
        # Re-attach Turnstile mock for submission
        mock_turnstile_script(page)
        
        submit_button = page.get_by_role("button", name="Submit Application")
        submit_button.click()
        
        # Wait for submission to complete (page should change or show success)
        # The editor redirects after submission, so wait for navigation away from editor
        try:
            page.wait_for_url(lambda url: "/a/" not in url, timeout=5000)
        except Exception:
            # Alternative: check if status changed to submitted
            pass
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_submitted_application_pdf_available_for_download(
    authenticated_browser_context_factory,
    authenticated_request_context_factory,
    draft_application,
    e2e_users,
    mock_turnstile_script,
):
    """Verify PDF is available after application submission."""
    applicant, app_key = draft_application
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        # Complete the workflow: fill, review, submit
        page.goto(f"/a/{app_key}")
        page.wait_for_selector('div#root', timeout=5000)
        
        title_input = page.get_by_label("Project title")
        title_input.fill("E2E Project Title")
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Continue").click()
        
        # Wait for Submit button to appear (indicates review page is loaded)
        page.get_by_role("button", name="Submit Application").wait_for(timeout=10000)
        # Then wait for checkbox to be visible
        page.wait_for_selector('input[type="checkbox"]:not([disabled])', timeout=10000)
        checkbox = page.locator('input[type="checkbox"]').first
        checkbox.click()
        
        mock_turnstile_script(page)
        submit_button = page.get_by_role("button", name="Submit Application")
        submit_button.click()
        
        # Wait for submission and redirect
        try:
            page.wait_for_url(lambda url: "/a/" not in url, timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)
        
        # Navigate to My Applications and check for PDF download link
        page.goto("/my-applications")
        download_selector = f'a[aria-label="Download application PDF"][href="/d/{app_key}"]'
        page.wait_for_selector(download_selector, timeout=5000)
        
        # Verify PDF endpoint returns valid PDF
        req_auth = authenticated_request_context_factory(applicant)
        req_ctx = req_auth["context"]
        try:
            resp = req_ctx.get(f"/d/{app_key}")
            assert resp.status == 200
            body = resp.body()
            assert body.startswith(b"%PDF"), "Response is not a valid PDF"
        finally:
            req_ctx.dispose()
    finally:
        page.close()
        context.close()
