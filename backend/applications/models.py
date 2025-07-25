from django.db import models


class ApplicationStatus(models.TextChoices):
    """Enumeration of possible application statuses."""

    NEW = "NEW"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Application(models.Model):
    """Model to represent an application."""

    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    questionnaire = models.ForeignKey(
        "questionnaires.Questionnaire",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Application by {self.user.username} for {self.questionnaire.name}"
