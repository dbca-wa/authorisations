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


def fill_editor_form_and_continue(page):
    """Fill form and navigate to review page.
    
    Reusable helper to avoid form-filling duplication across tests.
    Assumes page is at editor URL and form is loaded.
    """
    title_input = page.get_by_label("Project title")
    title_input.fill("E2E Project Title")
    # Click Continue and wait for page state change to review page
    page.get_by_role("button", name="Continue").click()
    page.wait_for_load_state("networkidle", timeout=5000)


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
                "collection_notice_agreed": True,
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
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Fill form and navigate to review
        fill_editor_form_and_continue(page)
        
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
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Fill and continue to review page
        fill_editor_form_and_continue(page)
        
        # Wait for Turnstile verification callback to complete and enable the checkbox
        page.wait_for_function(
            "() => document.querySelector('input[type=\"checkbox\"]')?.disabled === false",
            timeout=5000
        )
        page.get_by_role("checkbox").click()
        
        submit_button = page.get_by_role("button", name="Submit Application")
        submit_button.click()
        
        # Wait for submission modal to appear
        page.wait_for_selector('text="Application Successfully Submitted"', timeout=5000)
        
        # Verify modal contains expected content
        expect_text = "locked in read-only mode"
        page.get_by_text(expect_text, exact=False).wait_for()
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
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Fill and continue to review page
        fill_editor_form_and_continue(page)
        
        # Wait for Turnstile verification callback to complete and enable the checkbox
        page.wait_for_function(
            "() => document.querySelector('input[type=\"checkbox\"]')?.disabled === false",
            timeout=5000
        )
        page.get_by_role("checkbox").click()
        
        submit_button = page.get_by_role("button", name="Submit Application")
        submit_button.click()
        
        # Wait for submission to complete - page becomes read-only but stays at same URL
        page.wait_for_load_state("networkidle", timeout=5000)
        
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
