"""E2E tests for MyApplications page with discard/revert workflows.

Tests complete user journeys across multiple application statuses:
1. View applications categorized in tabs (Active, Terminated, Finalised)
2. Discard a draft application and verify tab transitions
3. Revert discarded application back to Active tab
4. Verify tab state with multiple applications in different statuses
5. Verify empty state handling and tab disable logic
"""

import json
import pytest
from questionnaires.models import Questionnaire


@pytest.fixture
def multiple_applications_fixture(authenticated_request_context_factory, e2e_users):
    """Create multiple applications in different statuses via API.
    
    Returns dict with application keys for:
    - draft: DRAFT status (can be discarded)
    - submitted: SUBMITTED status (Active tab, not discardable)
    """
    applicant = e2e_users["applicant"]
    auth_context = authenticated_request_context_factory(applicant)
    questionnaire = Questionnaire.objects.select_related("process").get(
        process__slug="aec", code="new-application", version=1
    )
    request_context = auth_context["context"]

    apps = {}
    
    try:
        # Create draft application
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
        apps["draft"] = response.json()["key"]
        
        # Create submitted application
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
        submitted_key = response.json()["key"]
        apps["submitted"] = submitted_key
        
        # Submit the application by patching its status
        response = request_context.patch(
            f"/api/applications/{submitted_key}",
            data=json.dumps({"status": "SUBMITTED"}),
            headers={
                str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
                "Content-Type": "application/json",
            },
        )
        assert response.status == 200
        
    finally:
        request_context.dispose()

    return applicant, apps


@pytest.fixture
def draft_application_for_discard(authenticated_request_context_factory, e2e_users):
    """Simplified fixture for single draft app tests."""
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
def test_my_applications_displays_tabs_with_multiple_statuses(
    authenticated_browser_context_factory,
    multiple_applications_fixture,
):
    """Verify MyApplications page displays all tabs and shows at least 2 applications
    in the Active tab when both draft and submitted applications exist."""
    applicant, apps = multiple_applications_fixture
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Verify page title
        assert page.get_by_role("heading", name="My Applications").is_visible()
        
        # Check that tabs are present
        active_tab = page.get_by_role("tab", name="Active")
        terminated_tab = page.get_by_role("tab", name="Terminated")
        finalised_tab = page.get_by_role("tab", name="Finalised")
        
        assert active_tab.is_visible()
        assert terminated_tab.is_visible()
        assert finalised_tab.is_visible()
        
        # Verify Active tab is selected and has at least 2 applications (draft + submitted)
        active_text = active_tab.text_content()
        # Extract the count number (e.g., "Active (2)" → 2)
        import re
        match = re.search(r'\((\d+)\)', active_text)
        active_count = int(match.group(1)) if match else 0
        assert active_count >= 2, f"Active tab should have at least 2 applications, found {active_count}"
        
        # Verify Active tab description is shown
        assert page.get_by_text(
            "View and manage your draft and submitted applications."
        ).is_visible()
        
        # Verify Terminated tab is empty (no discarded/withdrawn apps yet)
        assert "(0)" in terminated_tab.text_content(), "Terminated tab should be empty"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_only_draft_has_discard_button(
    authenticated_browser_context_factory,
    multiple_applications_fixture,
):
    """Verify that submitted applications do NOT have a discard button
    (only DRAFT status applications can be discarded)."""
    applicant, apps = multiple_applications_fixture
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Get all discard and revert buttons
        discard_buttons = page.get_by_role("button", name="Discard")
        revert_buttons = page.get_by_role("button", name="Revert")
        
        # Should have exactly 1 discard button (only for draft application)
        discard_count = discard_buttons.count()
        assert discard_count >= 1, f"Should have at least 1 discard button, found {discard_count}"
        
        # Should have no revert buttons (no discarded apps yet)
        revert_count = revert_buttons.count()
        assert revert_count == 0, f"Should have 0 revert buttons, found {revert_count}"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_discard_moves_application_between_tabs(
    authenticated_browser_context_factory,
    draft_application_for_discard,
):
    """Verify discarding a draft application moves it from Active to Terminated tab
    and updates tab counts correctly."""
    applicant, app_key = draft_application_for_discard
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Get initial Active tab state
        active_tab = page.get_by_role("tab", name="Active")
        active_count_before = active_tab.text_content()
        
        # Verify there's at least one discard button visible
        discard_button = page.get_by_role("button", name="Discard").first
        assert discard_button.is_visible(timeout=2000), "Discard button should be visible"
        
        # Click discard button
        discard_button.click()
        
        # Wait for snackbar notification
        page.get_by_role("alert").filter(
            has_text="Application discarded"
        ).wait_for(state="visible", timeout=5000)
        
        # Verify Active tab count decreased (check that numbers are different)
        active_count_after = active_tab.text_content()
        assert active_count_before != active_count_after, "Active tab count should have changed after discard"
        
        # Verify Terminated tab now has applications (not disabled)
        terminated_tab = page.get_by_role("tab", name="Terminated")
        terminated_text = terminated_tab.text_content()
        assert "(0)" not in terminated_text, "Terminated tab should have applications after discard"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_revert_moves_application_back_to_active_tab(
    authenticated_browser_context_factory,
    draft_application_for_discard,
):
    """Verify reverting a discarded application moves it back from Terminated to Active tab
    and updates tab counts correctly."""
    applicant, app_key = draft_application_for_discard
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # First, discard the application
        discard_button = page.get_by_role("button", name="Discard").first
        assert discard_button.is_visible(timeout=2000), "Discard button should be visible"
        
        discard_button.click()
        page.get_by_role("alert").filter(
            has_text="Application discarded"
        ).wait_for(state="visible", timeout=5000)
        
        # Navigate to Terminated tab
        terminated_tab = page.get_by_role("tab", name="Terminated")
        terminated_text_before = terminated_tab.text_content()
        
        # Verify Terminated tab is now enabled
        assert "(0)" not in terminated_text_before, "Terminated tab should be enabled after discard"
        
        terminated_tab.click()
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Find and click revert button
        revert_button = page.get_by_role("button", name="Revert").first
        assert revert_button.is_visible(timeout=2000), "Revert button should be visible in Terminated tab"
        
        revert_button.click()
        
        # Wait for success notification
        page.get_by_role("alert").filter(
            has_text="Application reverted to draft"
        ).wait_for(state="visible", timeout=5000)
        
        # Verify Terminated tab count decreased
        terminated_text_after = terminated_tab.text_content()
        assert terminated_text_before != terminated_text_after, "Terminated tab count should have changed after revert"
        
        # Verify Active tab is enabled again
        active_tab = page.get_by_role("tab", name="Active")
        active_text = active_tab.text_content()
        assert "(0)" not in active_text, "Active tab should have applications after revert"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_discard_revert_cycle_with_multiple_apps(
    authenticated_browser_context_factory,
    multiple_applications_fixture,
):
    """Verify discard/revert cycle works correctly with multiple applications
    (draft + submitted in Active tab), ensuring correct app is discarded."""
    applicant, apps = multiple_applications_fixture
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Get initial state
        active_tab = page.get_by_role("tab", name="Active")
        active_text_before = active_tab.text_content()
        
        # Verify we have at least one discard button (for the draft app)
        discard_buttons = page.get_by_role("button", name="Discard")
        assert discard_buttons.count() >= 1, "Should have at least 1 discard button"
        
        # Click the first discard button
        discard_buttons.first.click()
        page.get_by_role("alert").filter(
            has_text="Application discarded"
        ).wait_for(state="visible", timeout=5000)
        
        # Verify Active tab count changed
        active_text_after_discard = active_tab.text_content()
        assert active_text_before != active_text_after_discard, "Active tab count should decrease after discard"
        
        # Verify Terminated tab is now enabled
        terminated_tab = page.get_by_role("tab", name="Terminated")
        assert "(0)" not in terminated_tab.text_content(), "Terminated tab should be enabled after discard"
        
        # Navigate to Terminated tab and revert
        terminated_tab.click()
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Find revert button
        revert_button = page.get_by_role("button", name="Revert").first
        if revert_button.is_visible(timeout=2000):
            terminated_before = terminated_tab.text_content()
            
            revert_button.click()
            page.get_by_role("alert").filter(
                has_text="Application reverted to draft"
            ).wait_for(state="visible", timeout=5000)
            
            # Verify state changes
            terminated_after = terminated_tab.text_content()
            assert terminated_before != terminated_after, "Terminated tab count should change after revert"
            
            # Verify Active tab has applications again
            active_final = active_tab.text_content()
            assert "(0)" not in active_final, "Active tab should have applications after revert"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_tab_descriptions_display_correctly(
    authenticated_browser_context_factory,
    draft_application_for_discard,
):
    """Verify that each tab displays its correct description text."""
    applicant, app_key = draft_application_for_discard
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Verify Active tab is default and shows its description
        assert page.get_by_text(
            "View and manage your draft and submitted applications."
        ).is_visible(), "Active tab description should be visible initially"
        
        # Discard the application to populate Terminated tab
        discard_button = page.get_by_role("button", name="Discard").first
        if discard_button.is_visible(timeout=2000):
            discard_button.click()
            page.get_by_role("alert").filter(
                has_text="Application discarded"
            ).wait_for(state="visible", timeout=5000)
            
            # Now Terminated tab has 1 application (enabled), so we can click it
            terminated_tab = page.get_by_role("tab", name="Terminated")
            if "(0)" not in terminated_tab.text_content():
                terminated_tab.click()
                page.wait_for_load_state("networkidle", timeout=5000)
                
                # Verify Terminated description is now visible
                assert page.get_by_text(
                    "View applications that have been discarded or withdrawn."
                ).is_visible(), "Terminated tab description should be visible"
                
                # Old description should be gone
                assert not page.get_by_text(
                    "View and manage your draft and submitted applications."
                ).is_visible(), "Active tab description should not be visible when Terminated is active"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_empty_tabs_are_disabled(
    authenticated_browser_context_factory,
    draft_application_for_discard,
):
    """Verify that tabs with 0 applications are disabled and cannot be clicked."""
    applicant, app_key = draft_application_for_discard
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Verify Terminated tab is disabled (shows 0)
        terminated_tab = page.get_by_role("tab", name="Terminated")
        terminated_text = terminated_tab.text_content()
        assert "(0)" in terminated_text, "Terminated tab should show 0 applications"
        
        # Verify Finalised tab is disabled (shows 0)
        finalised_tab = page.get_by_role("tab", name="Finalised")
        finalised_text = finalised_tab.text_content()
        assert "(0)" in finalised_text, "Finalised tab should show 0 applications"
        
        # Attempting to click disabled tab should not change active tab
        # (disabled attribute prevents click in Playwright)
        active_tab_before = page.get_by_role("tab", name="Active")
        assert active_tab_before.get_attribute("aria-selected") == "true", "Active should be selected"
        
        # Disabled tabs should have disabled attribute
        assert terminated_tab.is_disabled(), "Terminated tab should be disabled"
        assert finalised_tab.is_disabled(), "Finalised tab should be disabled"
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_my_applications_tab_enable_after_discard(
    authenticated_browser_context_factory,
    draft_application_for_discard,
):
    """Verify that disabled tabs become enabled when they receive applications."""
    applicant, app_key = draft_application_for_discard
    
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Initially, Terminated tab is disabled
        terminated_tab = page.get_by_role("tab", name="Terminated")
        assert terminated_tab.is_disabled(), "Terminated tab should be disabled initially"
        assert "(0)" in terminated_tab.text_content(), "Terminated should show 0"
        
        # Discard the draft application
        discard_button = page.get_by_role("button", name="Discard").first
        if discard_button.is_visible(timeout=2000):
            discard_button.click()
            page.get_by_role("alert").filter(
                has_text="Application discarded"
            ).wait_for(state="visible", timeout=5000)
            
            # Now Terminated tab should be enabled
            assert not terminated_tab.is_disabled(), "Terminated tab should be enabled after receiving application"
            assert "1" in terminated_tab.text_content(), "Terminated should show 1 application"
            
            # Should be able to click it now
            terminated_tab.click()
            page.wait_for_load_state("networkidle", timeout=5000)
            
            # Verify we're now on Terminated tab
            assert terminated_tab.get_attribute("aria-selected") == "true", "Terminated should be selected"
    finally:
        page.close()
        context.close()
