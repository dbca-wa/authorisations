"""Integration tests for audit logging with ReviewerViewSet."""

import pytest
from rest_framework.test import APIClient

from applications.models import Application
from applications.statuses import ApplicationStatus
from audit.models import ApplicationAuditLog
from users.models import User


@pytest.mark.django_db
class TestReviewerViewSetAuditLogging:
    """Tests for audit logging integration with ReviewerViewSet.patch()."""

    @pytest.fixture
    def authenticated_reviewer_client(self, reviewer_user):
        """Return an authenticated APIClient for reviewer requests."""
        client = APIClient()
        client.force_authenticate(user=reviewer_user)
        return client

    @pytest.fixture
    def reviewer_user(self, reviewer_group):
        """Create a reviewer user."""
        user = User.objects.create_user(
            username="test_reviewer_001",
            email="reviewer@example.com",
            password="testpass123",
        )
        user.groups.add(reviewer_group)
        return user

    def test_reviewer_patch_creates_audit_log_submitted_to_under_review(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify audit log created when reviewer moves app from SUBMITTED to UNDER_REVIEW."""
        # Create an application owned by someone else
        other_user = User.objects.create_user(
            username="test_applicant_001",
            email="applicant@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.SUBMITTED
        )

        # Reviewer patches to UNDER_REVIEW
        response = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )

        assert response.status_code == 200
        # Verify audit log was created
        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs.count() == 1
        log = logs[0]
        assert log.user == reviewer_user
        assert log.prev_status == ApplicationStatus.SUBMITTED
        assert log.next_status == ApplicationStatus.UNDER_REVIEW

    def test_reviewer_patch_creates_audit_log_under_review_to_draft(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify audit log created when reviewer returns app to DRAFT."""
        other_user = User.objects.create_user(
            username="test_applicant_002",
            email="applicant2@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.UNDER_REVIEW
        )

        response = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.DRAFT},
            format="json",
        )

        assert response.status_code == 200
        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs.count() == 1
        log = logs[0]
        assert log.user == reviewer_user
        assert log.prev_status == ApplicationStatus.UNDER_REVIEW
        assert log.next_status == ApplicationStatus.DRAFT

    def test_reviewer_patch_creates_audit_log_under_review_to_assessment(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify audit log created when reviewer proceeds to UNDER_ASSESSMENT."""
        other_user = User.objects.create_user(
            username="test_applicant_003",
            email="applicant3@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.UNDER_REVIEW
        )

        response = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.UNDER_ASSESSMENT},
            format="json",
        )

        assert response.status_code == 200
        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs.count() == 1
        log = logs[0]
        assert log.user == reviewer_user
        assert log.prev_status == ApplicationStatus.UNDER_REVIEW
        assert log.next_status == ApplicationStatus.UNDER_ASSESSMENT

    def test_reviewer_patch_does_not_create_audit_log_on_validation_failure(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify audit log NOT created if PATCH validation fails."""
        other_user = User.objects.create_user(
            username="test_applicant_004",
            email="applicant4@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.DRAFT
        )

        # Try to set an invalid status transition
        response = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": "INVALID_STATUS"},
            format="json",
        )

        # Should fail validation
        assert response.status_code != 200
        # No audit log should be created
        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs.count() == 0

    def test_reviewer_patch_audit_log_captures_correct_user(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify audit log captures the actual reviewer who made the change."""
        other_user = User.objects.create_user(
            username="test_applicant_005",
            email="applicant5@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.SUBMITTED
        )

        response = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )

        assert response.status_code == 200
        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs[0].user.id == reviewer_user.id

    def test_multiple_reviewer_patches_creates_multiple_audit_logs(
        self, authenticated_reviewer_client, audit_application_factory, reviewer_user
    ):
        """Verify multiple status transitions create multiple audit logs."""
        other_user = User.objects.create_user(
            username="test_applicant_006",
            email="applicant6@example.com",
            password="testpass123",
        )
        app = audit_application_factory(
            owner=other_user, status=ApplicationStatus.SUBMITTED
        )

        # First patch: SUBMITTED -> UNDER_REVIEW
        response1 = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.UNDER_REVIEW},
            format="json",
        )
        assert response1.status_code == 200

        # Refresh application to get updated status
        app.refresh_from_db()

        # Second patch: UNDER_REVIEW -> UNDER_ASSESSMENT
        response2 = authenticated_reviewer_client.patch(
            f"/api/review/{app.key}",
            {"status": ApplicationStatus.UNDER_ASSESSMENT},
            format="json",
        )
        assert response2.status_code == 200

        # Verify both transitions were logged
        logs = ApplicationAuditLog.objects.filter(application=app).order_by(
            "timestamp"
        )
        assert logs.count() == 2
        assert logs[0].prev_status == ApplicationStatus.SUBMITTED
        assert logs[0].next_status == ApplicationStatus.UNDER_REVIEW
        assert logs[1].prev_status == ApplicationStatus.UNDER_REVIEW
        assert logs[1].next_status == ApplicationStatus.UNDER_ASSESSMENT
