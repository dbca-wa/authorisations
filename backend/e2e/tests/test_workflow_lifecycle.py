"""E2E tests covering the 'critical path' of the application lifecycle.

This module verifies the end-to-end flow described in STATUS-WORKFLOW.md:
Applicant (Draft -> Submit) -> Reviewer (Review/Triage -> Technical Assessment -> Return to Draft -> Re-submit -> Approve)
"""

import json
import time

import pytest
from applications import serialisers
from applications.models import Application
from applications.statuses import ApplicationStatus
from django.utils import timezone
from playwright.sync_api import expect


def _auth_json_headers(auth_context: dict[str, object]) -> dict[str, str]:
    """Build JSON request headers with CSRF from an authenticated E2E context."""
    return {
        str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
        "Content-Type": "application/json",
    }

@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestWorkflowLifecycle:
    """Test suite for the business-critical workflow lifecycle."""

    def test_applicant_submit_and_withdraw_api(
        self, authenticated_request_context_factory, e2e_users
    ):
        """Verify applicant can submit a draft and withdraw it if needed."""
        applicant = e2e_users["applicant"]
        app = Application.objects.filter(owner=applicant, status=ApplicationStatus.DRAFT).first()
        assert app is not None
        app_key = str(app.key)

        auth = authenticated_request_context_factory(applicant)
        req = auth["context"]
        headers = _auth_json_headers(auth)

        # Submit
        res = req.patch(
            f"/api/applications/{app_key}",
            data=json.dumps({"status": ApplicationStatus.SUBMITTED, "turnstile_token": "e2e-turnstile-token"}),
            headers=headers
        )
        assert res.status == 200
        assert Application.objects.get(key=app_key).status == ApplicationStatus.SUBMITTED

        # Withdraw
        res = req.patch(
            f"/api/applications/{app_key}",
            data=json.dumps({"status": ApplicationStatus.WITHDRAWN}),
            headers=headers
        )
        assert res.status == 200
        assert Application.objects.get(key=app_key).status == ApplicationStatus.WITHDRAWN

    def test_reviewer_triage_and_return_to_draft(
        self, authenticated_request_context_factory, e2e_users
    ):
        """
        Verify reviewer can triage (Under Review) and return to applicant (Draft).
        This verifies the 'Return to Draft' pattern that replaced 'Action Required'.
        Verify submitted_at is cleared when returning to DRAFT.
        """
        applicant = e2e_users["applicant"]
        reviewer = e2e_users["reviewer"]
        
        # Prepare a submitted app with submitted_at set
        app = Application.objects.filter(owner=applicant, status=ApplicationStatus.DRAFT).first()
        app.status = ApplicationStatus.SUBMITTED
        app.submitted_at = timezone.now()
        app.save()
        app_key = str(app.key)

        rev_auth = authenticated_request_context_factory(reviewer)
        req = rev_auth["context"]
        headers = _auth_json_headers(rev_auth)

        # Move to Under Review
        res = req.patch(
            f"/api/review/{app_key}",
            data=json.dumps({"status": ApplicationStatus.UNDER_REVIEW}),
            headers=headers
        )
        assert res.status == 200

        # Return to Draft (should clear submitted_at)
        res = req.patch(
            f"/api/review/{app_key}",
            data=json.dumps({"status": ApplicationStatus.DRAFT}),
            headers=headers
        )
        assert res.status == 200
        updated_app = Application.objects.get(key=app_key)
        assert updated_app.status == ApplicationStatus.DRAFT
        assert updated_app.submitted_at is None

    def test_full_progression_to_approval(
        self, authenticated_request_context_factory, e2e_users
    ):
        """
        Verify the complete workflow:
        1. Applicant Submits
        2. Assessor moves to Assessment
        3. Assessor Approves
        """
        applicant = e2e_users["applicant"]
        reviewer = e2e_users["reviewer"]
        
        app = Application.objects.filter(owner=applicant, status=ApplicationStatus.DRAFT).first()
        app_key = str(app.key)

        # 1. Applicant Submits
        app_auth = authenticated_request_context_factory(applicant)
        res = app_auth["context"].patch(
            f"/api/applications/{app_key}",
            data=json.dumps({"status": ApplicationStatus.SUBMITTED, "turnstile_token": "e2e-turnstile-token"}),
            headers=_auth_json_headers(app_auth)
        )
        assert res.status == 200

        # 2. Reviewer Approves
        rev_auth = authenticated_request_context_factory(reviewer)
        req = rev_auth["context"]
        headers = _auth_json_headers(rev_auth)

        # SUBMITTED -> UNDER_REVIEW
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_REVIEW}), headers=headers)
        assert res.status == 200

        # UNDER_REVIEW -> UNDER_ASSESSMENT
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_ASSESSMENT}), headers=headers)
        assert res.status == 200

        # UNDER_ASSESSMENT -> APPROVED
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.APPROVED}), headers=headers)
        assert res.status == 200
        assert Application.objects.get(key=app_key).status == ApplicationStatus.APPROVED

    def test_return_to_draft_and_resubmission_cycle(
        self, authenticated_request_context_factory, e2e_users, monkeypatch
    ):
        """
        Verify the full 'Return to Draft + Re-submission' cycle:
        1. Applicant Submits (sets submitted_at)
        2. Reviewer returns to Draft (clears submitted_at)
        3. Applicant Re-edits and Re-submits (sets NEW submitted_at with fresh timestamp)
        4. Reviewer approves
        """
        monkeypatch.setattr(serialisers, "verify_turnstile_token", lambda *args, **kwargs: True)

        applicant = e2e_users["applicant"]
        reviewer = e2e_users["reviewer"]
        
        app = Application.objects.filter(owner=applicant, status=ApplicationStatus.DRAFT).first()
        app_key = str(app.key)

        # 1. Applicant Submits
        app_auth = authenticated_request_context_factory(applicant)
        res = app_auth["context"].patch(
            f"/api/applications/{app_key}",
            data=json.dumps({"status": ApplicationStatus.SUBMITTED, "turnstile_token": "e2e-turnstile-token"}),
            headers=_auth_json_headers(app_auth)
        )
        assert res.status == 200
        original_submitted_at = Application.objects.get(key=app_key).submitted_at

        # 2. Reviewer returns to Draft
        rev_auth = authenticated_request_context_factory(reviewer)
        req = rev_auth["context"]
        headers = _auth_json_headers(rev_auth)
        
        res = req.patch(
            f"/api/review/{app_key}",
            data=json.dumps({"status": ApplicationStatus.UNDER_REVIEW}),
            headers=headers
        )
        assert res.status == 200
        
        res = req.patch(
            f"/api/review/{app_key}",
            data=json.dumps({"status": ApplicationStatus.DRAFT}),
            headers=headers
        )
        assert res.status == 200
        assert Application.objects.get(key=app_key).status == ApplicationStatus.DRAFT

        # 3. Applicant Re-submits (after editing in DRAFT)
        time.sleep(0.1)  # Small delay to ensure different timestamp
        
        app_auth = authenticated_request_context_factory(applicant)  # Refresh CSRF context
        res = app_auth["context"].patch(
            f"/api/applications/{app_key}",
            data=json.dumps({"status": ApplicationStatus.SUBMITTED, "turnstile_token": "e2e-turnstile-token"}),
            headers=_auth_json_headers(app_auth)
        )
        assert res.status == 200
        
        # Verify submitted_at is set to a NEW timestamp (not the original)
        resubmitted_app = Application.objects.get(key=app_key)
        assert resubmitted_app.submitted_at is not None
        assert resubmitted_app.submitted_at > original_submitted_at

        # 4. Reviewer approves
        rev_auth = authenticated_request_context_factory(reviewer)  # Refresh CSRF context
        req = rev_auth["context"]
        headers = _auth_json_headers(rev_auth)
        
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_REVIEW}), headers=headers)
        assert res.status == 200
        
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_ASSESSMENT}), headers=headers)
        assert res.status == 200
        
        res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.APPROVED}), headers=headers)
        assert res.status == 200
        assert Application.objects.get(key=app_key).status == ApplicationStatus.APPROVED

    def test_all_decision_outcomes(
        self, authenticated_request_context_factory, e2e_users, monkeypatch
    ):
        """
        Verify all reviewer decision outcomes are accessible:
        APPROVED, APPROVED_WITH_CONDITIONS, REJECTED, DEFERRED
        """
        monkeypatch.setattr(serialisers, "verify_turnstile_token", lambda *args, **kwargs: True)

        applicant = e2e_users["applicant"]
        reviewer = e2e_users["reviewer"]
        
        outcomes = [
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.REJECTED,
            ApplicationStatus.DEFERRED,
        ]
        
        for outcome in outcomes:
            # Create a new draft app for each outcome test
            app = Application.objects.filter(owner=applicant, status=ApplicationStatus.DRAFT).first()
            if app is None:
                continue  # Skip if no draft app available
            
            app_key = str(app.key)
            
            # Applicant submits
            app_auth = authenticated_request_context_factory(applicant)
            res = app_auth["context"].patch(
                f"/api/applications/{app_key}",
                data=json.dumps({"status": ApplicationStatus.SUBMITTED, "turnstile_token": "e2e-turnstile-token"}),
                headers=_auth_json_headers(app_auth)
            )
            assert res.status == 200
            
            # Reviewer progresses through review workflow
            rev_auth = authenticated_request_context_factory(reviewer)
            req = rev_auth["context"]
            headers = _auth_json_headers(rev_auth)
            
            res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_REVIEW}), headers=headers)
            assert res.status == 200
            
            res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": ApplicationStatus.UNDER_ASSESSMENT}), headers=headers)
            assert res.status == 200
            
            # Test the specific outcome
            res = req.patch(f"/api/review/{app_key}", data=json.dumps({"status": outcome}), headers=headers)
            assert res.status == 200, f"Failed to set outcome {outcome}"
            assert Application.objects.get(key=app_key).status == outcome

@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_workflow_ui_smoke(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Smoke test to ensure the review UI loads and displays submitted applications."""
    reviewer = e2e_users["reviewer"]
    
    # Ensure a submitted app exists
    app = Application.objects.filter(status=ApplicationStatus.SUBMITTED).first()
    if not app:
        app = Application.objects.first()
        app.status = ApplicationStatus.SUBMITTED
        app.save()

    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()
    page.goto("/review")
    
    # Wait for the view to render
    page.wait_for_selector('button[aria-label="View attachments"]')
    
    # Check for the "Submitted" status chip
    status_locator = page.get_by_text("Submitted", exact=True).first
    expect(status_locator).to_be_visible()

    page.close()
    context.close()
