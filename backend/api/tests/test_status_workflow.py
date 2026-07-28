"""Workflow-centric tests for application status transitions and business logic.

This module verifies the Transition Responsibility Matrix and basic business rules
defined in docs/STATUS-WORKFLOW.md.
"""

from datetime import timedelta

import pytest
from applications.models import Application, ApplicationStatus
from django.utils import timezone
from rest_framework import status

pytestmark = [pytest.mark.api, pytest.mark.django_db]


@pytest.fixture
def workflow_app(user, questionnaire_factory, application_factory):
    """Return a draft application owned by the test user."""
    return application_factory(
        owner=user,
        questionnaire=questionnaire_factory(),
        status=ApplicationStatus.DRAFT,
    )


@pytest.fixture
def reviewable_app(
    reviewer_group, process_factory, questionnaire_factory, application_factory
):
    """Return a submitted application in a process the reviewer group can review."""
    process = process_factory()
    process.reviewer_groups.add(reviewer_group)
    return application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )


class TestApplicantTransitions:
    """Test transitions initiated by the application owner."""

    def test_submit_draft_success(self, api_client, user, workflow_app, monkeypatch):
        """Allow owner to transition DRAFT to SUBMITTED."""
        # Mock turnstile verification for submission
        from applications import serialisers

        monkeypatch.setattr(
            serialisers, "verify_turnstile_token", lambda *args, **kwargs: True
        )

        api_client.force_authenticate(user=user)
        response = api_client.patch(
            f"/api/applications/{workflow_app.key}",
            {"status": ApplicationStatus.SUBMITTED, "turnstile_token": "valid"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        workflow_app.refresh_from_db()
        assert workflow_app.status == ApplicationStatus.SUBMITTED
        assert workflow_app.submitted_at is not None

    def test_withdraw_anytime_before_decision(self, api_client, user, workflow_app):
        """Allow owner to transition SUBMITTED/UNDER_REVIEW to WITHDRAWN."""
        api_client.force_authenticate(user=user)

        # Test withdrawing from SUBMITTED
        workflow_app.status = ApplicationStatus.SUBMITTED
        workflow_app.save()

        response = api_client.patch(
            f"/api/applications/{workflow_app.key}",
            {"status": ApplicationStatus.WITHDRAWN},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_bypass_triage(self, api_client, user, workflow_app):
        """Reject owner attempts to skip straight to technical review or decision."""
        api_client.force_authenticate(user=user)
        forbidden = [
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.UNDER_ASSESSMENT,
            ApplicationStatus.APPROVED,
        ]

        for target in forbidden:
            response = api_client.patch(
                f"/api/applications/{workflow_app.key}",
                {"status": target},
                format="json",
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_discard_draft_application(self, api_client, user, workflow_app):
        """Allow owner to discard a draft application."""
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            f"/api/applications/{workflow_app.key}",
            {"status": ApplicationStatus.DISCARDED},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        workflow_app.refresh_from_db()
        assert workflow_app.status == ApplicationStatus.DISCARDED

    def test_withdraw_during_review(self, api_client, user, reviewable_app):
        """Allow owner to withdraw application while under review."""
        api_client.force_authenticate(user=user)
        reviewable_app.owner = user  # Make user the owner
        reviewable_app.status = ApplicationStatus.UNDER_REVIEW
        reviewable_app.save()

        response = api_client.patch(
            f"/api/applications/{reviewable_app.key}",
            {"status": ApplicationStatus.WITHDRAWN},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.WITHDRAWN

    def test_withdraw_during_assessment(self, api_client, user, reviewable_app):
        """Allow owner to withdraw application during review phase."""
        api_client.force_authenticate(user=user)
        reviewable_app.owner = user  # Make user the owner
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/applications/{reviewable_app.key}",
            {"status": ApplicationStatus.WITHDRAWN},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.WITHDRAWN

    def test_cannot_transition_from_terminal_state(
        self, api_client, user, workflow_app
    ):
        """Reject attempts to transition from terminal states (APPROVED, REJECTED, etc.)."""
        api_client.force_authenticate(user=user)

        for terminal_status in [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.DEFERRED,
            ApplicationStatus.WITHDRAWN,
        ]:
            workflow_app.status = terminal_status
            workflow_app.save()

            response = api_client.patch(
                f"/api/applications/{workflow_app.key}",
                {"status": ApplicationStatus.DRAFT},
                format="json",
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestReviewerTransitions:
    """Test transitions initiated by technical officers (Reviewers)."""

    def test_staff_workflow_progression(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Staff can move app through SUBMITTED -> UNDER_REVIEW -> UNDER_ASSESSMENT."""
        api_client.force_authenticate(user=reviewer_user)

        # 1. Claim app
        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. To Technical Assessment
        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.UNDER_ASSESSMENT},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_return_to_draft_unlocks_editing(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Verify 'Return to Draft' from UNDER_REVIEW allows applicant to edit again."""
        api_client.force_authenticate(user=reviewer_user)

        # First, transition SUBMITTED -> UNDER_REVIEW (required per workflow)
        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # Now return to DRAFT from UNDER_REVIEW
        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.DRAFT},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.DRAFT

    def test_reviewer_approve_decision(self, api_client, reviewer_user, reviewable_app):
        """Allow reviewer to approve an application under assessment."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.APPROVED},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.APPROVED

    def test_reviewer_approve_with_conditions_decision(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Allow reviewer to approve with conditions."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.APPROVED_WITH_CONDITIONS},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.APPROVED_WITH_CONDITIONS

    def test_reviewer_reject_decision(self, api_client, reviewer_user, reviewable_app):
        """Allow reviewer to reject an application."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.REJECTED},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.REJECTED

    def test_reviewer_defer_decision(self, api_client, reviewer_user, reviewable_app):
        """Allow reviewer to defer an application under assessment for later decision."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.DEFERRED},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.DEFERRED

    def test_return_to_draft_from_under_assessment(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Verify 'Return to Draft' from UNDER_ASSESSMENT for re-submission."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        # Return to DRAFT from UNDER_ASSESSMENT
        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.DRAFT},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        reviewable_app.refresh_from_db()
        assert reviewable_app.status == ApplicationStatus.DRAFT

    def test_reviewer_cannot_set_applicant_only_transitions(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Reject reviewer attempts to set applicant-only statuses like DISCARDED."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.SUBMITTED
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.DISCARDED},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_skip_review_queue_progression(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Reject transitions that skip required workflow steps (e.g. SUBMITTED → UNDER_ASSESSMENT)."""
        api_client.force_authenticate(user=reviewer_user)
        # Application is in SUBMITTED; cannot jump directly to UNDER_ASSESSMENT

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.UNDER_ASSESSMENT},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_reverse_from_under_assessment_to_under_review(
        self, api_client, reviewer_user, reviewable_app
    ):
        """Reject backwards progression UNDER_ASSESSMENT → UNDER_REVIEW."""
        api_client.force_authenticate(user=reviewer_user)
        reviewable_app.status = ApplicationStatus.UNDER_ASSESSMENT
        reviewable_app.save()

        response = api_client.patch(
            f"/api/review/{reviewable_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestWorkflowBusinessRules:
    """Test cross-cutting concerns like immutability and submission timestamps."""

    def test_read_only_when_not_draft(self, api_client, user, workflow_app):
        """Reject document updates (PUT) for any status other than DRAFT."""
        api_client.force_authenticate(user=user)
        workflow_app.status = ApplicationStatus.SUBMITTED
        workflow_app.save()

        payload = {"schema_version": "1", "active_step": 0, "steps": []}

        response = api_client.put(
            f"/api/applications/{workflow_app.key}",
            {"document": payload},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot modify document with status" in str(response.data)

    def test_submitted_at_preservation(
        self, api_client, user, workflow_app, monkeypatch
    ):
        """Ensure re-submission doesn't overwrite the original submitted_at timestamp."""
        from applications import serialisers

        monkeypatch.setattr(
            serialisers, "verify_turnstile_token", lambda *args, **kwargs: True
        )

        original_time = timezone.now() - timedelta(days=1)
        workflow_app.submitted_at = original_time
        workflow_app.save()

        api_client.force_authenticate(user=user)
        api_client.patch(
            f"/api/applications/{workflow_app.key}",
            {"status": ApplicationStatus.SUBMITTED, "turnstile_token": "valid"},
            format="json",
        )

        workflow_app.refresh_from_db()
        # Should stay as original time (or at least not be updated to 'now')
        assert workflow_app.submitted_at == original_time

    def test_owner_cannot_set_staff_statuses(self, api_client, user, workflow_app):
        """Reject owner attempts to set staff-only statuses like UNDER_REVIEW."""
        api_client.force_authenticate(user=user)
        workflow_app.status = ApplicationStatus.SUBMITTED
        workflow_app.save()

        response = api_client.patch(
            f"/api/applications/{workflow_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_applicant_cannot_access_review_endpoint(
        self, api_client, user, workflow_app
    ):
        """Reject applicant access to the review endpoint (staff-only)."""
        api_client.force_authenticate(user=user)
        workflow_app.status = ApplicationStatus.SUBMITTED
        workflow_app.save()

        response = api_client.patch(
            f"/api/review/{workflow_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        # Should be 403 Forbidden or 404 Not Found depending on permission model
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_reviewer_cannot_act_on_unrelated_application(
        self, api_client, reviewer_user, workflow_app
    ):
        """Reject staff access if application is not in a process they can review."""
        api_client.force_authenticate(user=reviewer_user)
        # Application's process is not in reviewer_user's group
        workflow_app.status = ApplicationStatus.SUBMITTED
        workflow_app.save()

        response = api_client.patch(
            f"/api/review/{workflow_app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        # Should be 403 Forbidden or 404 Not Found
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]
