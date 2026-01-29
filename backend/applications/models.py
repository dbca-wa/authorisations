import uuid
from django.db import models
from django_jsonform.models.fields import JSONField

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

    # @staticmethod
    # def has_access(user, key: str) -> bool:
    #     return Application.objects.filter(
    #         key=key,
    #         owner=user,
    #     ).exists()


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

from django.utils import timezone

def attachment_upload_path(instance, filename):
    """Define the upload path for the attachment file."""
    return f"attachments/{instance.application.id}/{instance.key}/{filename}"

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
    file = models.FileField(upload_to=attachment_upload_path, blank=False, null=False)
    field = models.CharField(max_length=100, blank=False, null=False)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    deleted_at = models.DateTimeField(blank=True, null=True, editable=False)

    def soft_delete(self):
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Attachment {self.key} for Application {self.application.id}"

