"""Audit logging models for tracking application status changes."""

from django.conf import settings
from django.db import models

from applications.models import Application
from applications.statuses import ApplicationStatus


class ApplicationAuditLog(models.Model):
    """
    Audit log entry for application status changes.

    Records every transition of an application's status by a user, enabling
    regulatory compliance tracking and investigation of reviewer/assessor actions.
    """

    application = models.ForeignKey(
        Application,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        help_text="The application that changed status.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="The user who triggered the status change (null if system action).",
    )
    prev_status = models.CharField(
        max_length=50,
        choices=ApplicationStatus.choices,
        help_text="The application status before the change.",
    )
    next_status = models.CharField(
        max_length=50,
        choices=ApplicationStatus.choices,
        help_text="The application status after the change.",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the status change was recorded (UTC).",
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Application Audit Log"
        verbose_name_plural = "Application Audit Logs"
        indexes = [
            models.Index(fields=["application", "-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self) -> str:
        return (
            f"Application {self.application.key}: {self.prev_status} → "
            f"{self.next_status} by {self.user or 'system'} at {self.timestamp}"
        )


def record_application_status_change(
    application: Application,
    user,
    prev_status: str,
    next_status: str,
) -> ApplicationAuditLog | None:
    """
    Record an application status change to the audit log.

    Only creates a log entry if the status actually changed (prev_status != next_status).
    This helper function provides a single point of control for audit logging throughout
    the codebase, ensuring consistency and making it easy to disable or modify logging
    behaviour across all transitions.

    Args:
        application: The Application instance that changed.
        user: The User who triggered the change (can be None for system actions).
        prev_status: The previous ApplicationStatus value (must be a valid choice).
        next_status: The new ApplicationStatus value (must be a valid choice).

    Returns:
        The created ApplicationAuditLog instance if status changed, None otherwise.

    Raises:
        ValueError: If prev_status or next_status are not valid ApplicationStatus choices.
    """
    # Validate that statuses are valid choices
    valid_statuses = {choice[0] for choice in ApplicationStatus.choices}
    if prev_status not in valid_statuses:
        raise ValueError(f"Invalid previous status: {prev_status}")
    if next_status not in valid_statuses:
        raise ValueError(f"Invalid next status: {next_status}")

    # Only log if status actually changed
    if prev_status == next_status:
        return None

    return ApplicationAuditLog.objects.create(
        application=application,
        user=user,
        prev_status=prev_status,
        next_status=next_status,
    )
