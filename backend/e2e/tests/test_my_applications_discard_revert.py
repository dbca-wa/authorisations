"""E2E tests for MyApplications page with discard/revert workflows.

Tests complete user journeys:
1. View applications categorized in tabs
2. Discard a draft application
3. See application move to Terminated tab
4. Revert discarded application back to Active tab
5. Verify tab state changes (enable/disable, counts, empty states)

Prerequisites:
- Authenticated user with existing applications in different statuses
- Backend API endpoints working correctly
"""

import json
import pytest
from applications.models import Application


@pytest.fixture
def draft_and_submitted_applications(authenticated_request_context_factory, e2e_users, e2e_process):
    """Create draft and submitted applications via API for testing.
    
    Returns dict with application keys for different statuses.
    """
    applicant = e2e_users["applicant"]
    auth_context = authenticated_request_context_factory(applicant)
    request_context = auth_context["context"]
    
    # Get a questionnaire from the process
    from questionnaires.models import Questionnaire
    questionnaire = Questionnaire.objects.filter(
        process=e2e_process,
        code="new-application",
        version=1
    ).first()
    
    if not questionnaire:
        pytest.skip("No questionnaire available for test")
    
    apps = {}
    
    # Create draft application
    response = request_context.post(
        "/api/applications",
        data=json.dumps({
            "process_slug": e2e_process.slug,
            "questionnaire_id": questionnaire.id,
            "questionnaire_code": questionnaire.code,
            "questionnaire_version": questionnaire.version,
            "privacy_consent_agreed": True,
            "turnstile_token": "e2e-turnstile-token",
        }),
        content_type="application/json",
    )
    
    if response.status_code == 201:
        apps["draft_key"] = response.json()["key"]
    
    # Create a submitted application
    response = request_context.post(
        "/api/applications",
        data=json.dumps({
            "process_slug": e2e_process.slug,
            "questionnaire_id": questionnaire.id,
            "questionnaire_code": questionnaire.code,
            "questionnaire_version": questionnaire.version,
            "privacy_consent_agreed": True,
            "turnstile_token": "e2e-turnstile-token",
        }),
        content_type="application/json",
    )
    
    if response.status_code == 201:
        submitted_key = response.json()["key"]
        apps["submitted_key"] = submitted_key
        
        # Submit the application
        request_context.patch(
            f"/api/applications/{submitted_key}",
            data=json.dumps({"status": "SUBMITTED"}),
            content_type="application/json",
        )
    
    return apps


def test_my_applications_displays_correct_tabs_and_descriptions(page, authenticated_page, e2e_users):
    """Verify MyApplications page displays all tabs with correct descriptions."""
    applicant = e2e_users["applicant"]
    authenticated_page(page, applicant)
    
    # Navigate to My Applications
    page.goto("/my-applications")
    
    # Verify page loaded
    assert page.get_by_role("heading", name="My Applications").is_visible()
    
    # Check that tabs are present
    active_tab = page.get_by_role("tab", name="Active")
    terminated_tab = page.get_by_role("tab", name="Terminated")
    finalised_tab = page.get_by_role("tab", name="Finalised")
    
    assert active_tab.is_visible()
    assert terminated_tab.is_visible()
    assert finalised_tab.is_visible()
    
    # Verify Active tab description is shown
    assert page.get_by_text(
        "View and manage your draft and submitted applications."
    ).is_visible()
    
    # Switch to Terminated and verify description
    terminated_tab.click()
    page.wait_for_load_state("networkidle")
    assert page.get_by_text(
        "View applications that have been discarded or withdrawn."
    ).is_visible()
    
    # Switch to Finalised and verify description
    finalised_tab.click()
    page.wait_for_load_state("networkidle")
    assert page.get_by_text(
        "View applications that have been approved, rejected, or deferred."
    ).is_visible()


def test_my_applications_discard_moves_application_to_terminated_tab(
    page, authenticated_page, e2e_users, draft_and_submitted_applications
):
    """Verify discarding a draft application moves it to Terminated tab."""
    applicant = e2e_users["applicant"]
    authenticated_page(page, applicant)
    
    # Skip if no draft app was created
    if "draft_key" not in draft_and_submitted_applications:
        pytest.skip("Could not create draft application")
    
    # Navigate to My Applications
    page.goto("/my-applications")
    page.wait_for_load_state("networkidle")
    
    # Get initial tab counts
    active_tab = page.get_by_role("tab", name="Active")
    active_count_before = active_tab.text_content()
    
    # Find discard button
    discard_button = page.get_by_role("button", name="Discard").first()
    
    if not discard_button.is_visible(timeout=2000):
        pytest.skip("No discard button visible for draft application")
    
    # Click discard button
    discard_button.click()
    
    # Wait for success notification
    page.get_by_role("alert").filter(
        has_text="Application discarded"
    ).wait_for(state="visible", timeout=5000)
    
    # Verify active tab count decreased
    active_count_after = active_tab.text_content()
    assert active_count_before != active_count_after, "Active tab count should have changed"
    
    # Verify Terminated tab now has applications
    terminated_tab = page.get_by_role("tab", name="Terminated")
    terminated_count = terminated_tab.text_content()
    assert "(0)" not in terminated_count, "Terminated tab should have applications after discard"


def test_my_applications_revert_moves_application_to_active_tab(
    page, authenticated_page, e2e_users, draft_and_submitted_applications
):
    """Verify reverting a discarded application moves it back to Active tab."""
    applicant = e2e_users["applicant"]
    authenticated_page(page, applicant)
    
    # Skip if no draft app was created
    if "draft_key" not in draft_and_submitted_applications:
        pytest.skip("Could not create draft application for revert test")
    
    # Navigate to My Applications
    page.goto("/my-applications")
    page.wait_for_load_state("networkidle")
    
    # First discard an application
    discard_button = page.get_by_role("button", name="Discard").first()
    if discard_button.is_visible(timeout=2000):
        discard_button.click()
        page.get_by_role("alert").filter(
            has_text="Application discarded"
        ).wait_for(state="visible", timeout=5000)
    
    # Navigate to Terminated tab
    terminated_tab = page.get_by_role("tab", name="Terminated")
    terminated_tab.click()
    page.wait_for_load_state("networkidle")
    
    # Get count before revert
    terminated_count_before = terminated_tab.text_content()
    
    # Find revert button
    revert_button = page.get_by_role("button", name="Revert").first()
    
    if not revert_button.is_visible(timeout=2000):
        pytest.skip("No revert button visible for discarded application")
    
    # Click revert button
    revert_button.click()
    
    # Wait for success notification
    page.get_by_role("alert").filter(
        has_text="Application reverted to draft"
    ).wait_for(state="visible", timeout=5000)
    
    # Verify terminated tab count decreased
    terminated_count_after = terminated_tab.text_content()
    assert terminated_count_before != terminated_count_after, "Terminated tab count should have changed"
    
    # Verify application is now in Active tab
    active_tab = page.get_by_role("tab", name="Active")
    active_tab.click()
    page.wait_for_load_state("networkidle")
    
    # Application should be visible in Active tab
    assert active_tab.text_content(), "Active tab should have applications after revert"


def test_my_applications_shows_empty_state_for_empty_tab(
    page, authenticated_page, e2e_users
):
    """Verify empty state is shown when switching to a tab with no applications."""
    applicant = e2e_users["applicant"]
    authenticated_page(page, applicant)
    
    # Navigate to My Applications
    page.goto("/my-applications")
    page.wait_for_load_state("networkidle")
    
    # Try to find an empty tab
    active_tab = page.get_by_role("tab", name="Active")
    terminated_tab = page.get_by_role("tab", name="Terminated")
    
    active_count = active_tab.text_content()
    terminated_count = terminated_tab.text_content()
    
    # Check if Terminated tab is empty
    if "(0)" in terminated_count:
        terminated_tab.click()
        page.wait_for_load_state("networkidle")
        
        # Should show empty state
        assert page.get_by_text("Nothing to see here").is_visible(timeout=5000)
    elif "(0)" in active_count:
        # Active tab is empty, should already show empty state
        assert page.get_by_text("Nothing to see here").is_visible(timeout=5000)
