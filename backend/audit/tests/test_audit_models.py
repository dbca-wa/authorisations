"""Unit tests for audit logging."""

import pytest
from django.utils import timezone

from applications.models import Application
from applications.statuses import ApplicationStatus
from audit.models import ApplicationAuditLog, record_application_status_change
from users.models import User


@pytest.mark.django_db
class TestApplicationAuditLog:
    """Tests for ApplicationAuditLog model."""

    def test_audit_log_created_on_valid_status_change(self, application_factory, user):
        """Verify that an audit log is created when status changes."""
        app = application_factory(status=ApplicationStatus.DRAFT)
        prev_status = app.status
        app.status = ApplicationStatus.SUBMITTED
        app.save()

        log = record_application_status_change(app, user, prev_status, app.status)

        assert log is not None
        assert log.application == app
        assert log.user == user
        assert log.prev_status == ApplicationStatus.DRAFT
        assert log.next_status == ApplicationStatus.SUBMITTED
        assert log.timestamp is not None

    def test_audit_log_not_created_on_no_op_transition(self, application_factory, user):
        """Verify that no audit log is created if status doesn't change."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        log = record_application_status_change(
            app, user, ApplicationStatus.DRAFT, ApplicationStatus.DRAFT
        )

        assert log is None
        assert not ApplicationAuditLog.objects.filter(application=app).exists()

    def test_audit_log_captures_correct_fields(self, application_factory, user):
        """Verify that audit log captures all required fields correctly."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        log = record_application_status_change(
            app,
            user,
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
        )

        assert log.application.id == app.id
        assert log.user.id == user.id
        assert log.prev_status == ApplicationStatus.DRAFT
        assert log.next_status == ApplicationStatus.SUBMITTED
        # Timestamp should be set to now (within a few seconds)
        assert abs((timezone.now() - log.timestamp).total_seconds()) < 5

    def test_audit_log_with_null_user(self, application_factory):
        """Verify that audit log can be created with null user for system actions."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        log = record_application_status_change(
            app,
            None,
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
        )

        assert log is not None
        assert log.user is None
        assert log.prev_status == ApplicationStatus.DRAFT
        assert log.next_status == ApplicationStatus.SUBMITTED

    def test_audit_log_string_representation(self, application_factory, user):
        """Verify that __str__ produces a meaningful representation."""
        app = application_factory(status=ApplicationStatus.DRAFT)
        log = record_application_status_change(
            app,
            user,
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
        )

        str_repr = str(log)
        assert str(app.key) in str_repr
        assert "DRAFT" in str_repr
        assert "SUBMITTED" in str_repr
        assert user.email in str_repr

    def test_audit_log_queryable_by_application(self, application_factory, user):
        """Verify that we can query audit logs by application."""
        app1 = application_factory(status=ApplicationStatus.DRAFT)
        app2 = application_factory(status=ApplicationStatus.DRAFT)

        # Create logs for both applications
        record_application_status_change(
            app1, user, ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED
        )
        record_application_status_change(
            app2, user, ApplicationStatus.DRAFT, ApplicationStatus.UNDER_REVIEW
        )

        # Verify we can filter by application
        logs_for_app1 = ApplicationAuditLog.objects.filter(application=app1)
        logs_for_app2 = ApplicationAuditLog.objects.filter(application=app2)

        assert logs_for_app1.count() == 1
        assert logs_for_app2.count() == 1
        assert logs_for_app1[0].next_status == ApplicationStatus.SUBMITTED
        assert logs_for_app2[0].next_status == ApplicationStatus.UNDER_REVIEW

    def test_audit_log_queryable_by_user(self, application_factory):
        """Verify that we can query audit logs by user."""
        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        app1 = application_factory(status=ApplicationStatus.DRAFT)
        app2 = application_factory(status=ApplicationStatus.DRAFT)

        # Create logs by different users
        record_application_status_change(
            app1, user1, ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED
        )
        record_application_status_change(
            app2, user2, ApplicationStatus.DRAFT, ApplicationStatus.UNDER_REVIEW
        )

        # Verify we can filter by user
        logs_by_user1 = ApplicationAuditLog.objects.filter(user=user1)
        logs_by_user2 = ApplicationAuditLog.objects.filter(user=user2)

        assert logs_by_user1.count() == 1
        assert logs_by_user2.count() == 1
        assert logs_by_user1[0].application == app1
        assert logs_by_user2[0].application == app2

    def test_audit_log_ordered_by_timestamp_descending(self, application_factory, user):
        """Verify that audit logs are ordered by timestamp (newest first)."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        # Create multiple logs
        record_application_status_change(
            app, user, ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED
        )
        record_application_status_change(
            app, user, ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW
        )
        record_application_status_change(
            app, user, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED
        )

        logs = ApplicationAuditLog.objects.filter(application=app)
        assert logs.count() == 3
        # Default ordering should be descending (newest first)
        assert logs[0].next_status == ApplicationStatus.APPROVED
        assert logs[1].next_status == ApplicationStatus.UNDER_REVIEW
        assert logs[2].next_status == ApplicationStatus.SUBMITTED


@pytest.mark.django_db
class TestRecordApplicationStatusChangeHelper:
    """Tests for record_application_status_change helper function."""

    def test_invalid_prev_status_raises_error(self, application_factory, user):
        """Verify that invalid prev_status raises ValueError."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        with pytest.raises(ValueError) as exc_info:
            record_application_status_change(
                app, user, "INVALID_STATUS", ApplicationStatus.SUBMITTED
            )

        assert "Invalid previous status" in str(exc_info.value)

    def test_invalid_next_status_raises_error(self, application_factory, user):
        """Verify that invalid next_status raises ValueError."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        with pytest.raises(ValueError) as exc_info:
            record_application_status_change(
                app, user, ApplicationStatus.DRAFT, "INVALID_STATUS"
            )

        assert "Invalid next status" in str(exc_info.value)

    def test_helper_function_returns_created_instance(self, application_factory, user):
        """Verify that helper function returns the created audit log."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        result = record_application_status_change(
            app, user, ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED
        )

        assert isinstance(result, ApplicationAuditLog)
        assert result.id is not None

    def test_helper_function_returns_none_on_no_change(self, application_factory, user):
        """Verify that helper function returns None if status doesn't change."""
        app = application_factory(status=ApplicationStatus.DRAFT)

        result = record_application_status_change(
            app, user, ApplicationStatus.DRAFT, ApplicationStatus.DRAFT
        )

        assert result is None
