import uuid

from django.db import models
from django.utils import timezone
from django_jsonform.models.fields import JSONField
from users.models import User

from .schema import get_answers_schema


class ApplicationStatus(models.TextChoices):
    """Enumeration of possible application statuses."""

    DRAFT = "DRAFT"
    DISCARDED = "DISCARDED"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Application(models.Model):
    """Model to represent an application."""

    id = models.BigAutoField(primary_key=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="applications",
        db_index=False,
        editable=False,
    )
    questionnaire = models.ForeignKey(
        "questionnaires.Questionnaire",
        on_delete=models.PROTECT,
        related_name="applications",
        db_index=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        editable=False,
    )
    document = JSONField(
        schema=get_answers_schema(),
        blank=False,
        null=False,
        editable=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    submitted_at = models.DateTimeField(blank=True, null=True, editable=False)

    # Create multiple column indexes for:
    # - user, status, created_at DESC
    # - questionnaire, status, created_at DESC
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["owner", "status", "-created_at"],
                name="apps_owner_status_idx",
            ),
            models.Index(
                fields=["questionnaire", "status", "-created_at"],
                name="apps_questionnaire_status_idx",
            ),
        ]

    def __str__(self):
        return f"Application #{self.id} by {self.owner.username} for {self.questionnaire.name}"

    def has_access(self, user: User) -> bool:
        """
        Returns True if the user has access to this application.
        - Owners always have access.
        - TODO: Extend this logic for Technical Officers or other roles in the future.
        """
        if not user.is_authenticated:
            return False

        if self.owner == user:
            return True

        # TODO: Add logic for Technical Officers or other roles
        return False


# def certificate_path(instance, filename):
#     """Define the upload path for the certificate file."""
#     return f"certificates/{instance.application.id}/{filename}"


# class ApplicationCertificate(models.Model):
#     """Model to represent a certificate issued for an application."""

#     application = models.OneToOneField(
#         Application,
#         primary_key=True,
#         on_delete=models.CASCADE,
#         related_name="certificate",
#     )
#     certificate = models.FileField(upload_to=certificate_path, blank=False, null=False)
#     issued_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Certificate for the application #{self.application.id} issued at {self.issued_at}"


def attachment_upload_path(instance, filename):
    """Define the upload path for the attachment file."""
    created_month = instance.application.created_at.strftime("%Y-%m")
    return f"attachments/{created_month}/{instance.application.key}/{instance.key}"


class ApplicationAttachment(models.Model):
    """Model to represent a file attached to an application."""

    id = models.BigAutoField(primary_key=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_index=True,
        editable=False,
    )
    question = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False)
    file = models.FileField(
        upload_to=attachment_upload_path,
        blank=False,
        null=False,
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    deleted_at = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        indexes = [
            models.Index(
                fields=["application", "is_deleted"],
                name="attachments_app_deleted_idx",
            ),
        ]

    def __str__(self):
        return f"Attachment {self.key} for Application {self.application.id}"

    def soft_delete(self):
        """
        Mark the attachment as deleted and record when.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def get_download_url(self, request):
        """Generate a download URL for this attachment."""
        return request.build_absolute_uri(f"/d/{self.application.key}/{self.key}")
