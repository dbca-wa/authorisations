from api.serialisers import JsonSchemaSerialiserMixin
from django.db import models
from django_jsonform.models.fields import JSONField
from rest_framework import serializers

from .schema import get_questionnaire_schema


class Questionnaire(models.Model):
    """Model to represent a questionnaire with steps, sections, and questions."""

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(
        max_length=20,
        null=False,
        blank=False,
        unique=False,
        db_index=False,
        editable=True,
    )
    version = models.PositiveSmallIntegerField(
        default=1, blank=False, null=False, editable=False
    )
    name = models.CharField(max_length=100, blank=False, null=False, editable=True)
    description = models.TextField(
        max_length=500, blank=False, null=False, editable=True
    )
    document = JSONField(
        schema=get_questionnaire_schema(),
        blank=False,
        null=False,
        editable=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "users.User",
        related_name="questionnaires",
        on_delete=models.PROTECT,
        editable=False,
    )
    members = models.ManyToManyField(
        "users.User",
        through="QuestionnaireMembership",
        related_name="+",
        blank=True,
        null=True,
        help_text="Users who participate in managing (or reporting) this questionnaire.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "slug",
                models.F("version").desc(),
                name="qnaire_unique_slug_version_desc",
                include=["name"],
            )
        ]

    def __str__(self):
        return f'Questionnaire "{self.name}" (v{self.version})'


class QuestionnairePermission(models.Model):
    """
    Declarative permissions for questionnaire membership.

    - codename: stable machine-readable identifier (used in code checks)
    - name: human-friendly label shown in the Django admin
    - description: free text explaining what this permission allows
    """

    id = models.BigAutoField(primary_key=True)
    codename = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Machine-readable permission identifier, e.g. 'view_applications'.",
    )
    name = models.CharField(max_length=255, help_text="Human readable permission name.")
    description = models.TextField(
        blank=True, default="", help_text="Optional description/help text."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("codename",)
        verbose_name = "Questionnaire permission"
        verbose_name_plural = "Questionnaire permissions"

    def __str__(self):
        return f"{self.name} ({self.codename})"


class QuestionnaireMembership(models.Model):
    """
    Through model for Questionnaire.members -> users.User.

    Stores role permissions and other metadata about the member relationship.
    """

    id = models.BigAutoField(primary_key=True)
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name="+",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="+",
    )
    permissions = models.ManyToManyField(
        QuestionnairePermission,
        blank=False,
        null=False,
        related_name="+",
        help_text="Permissions assigned to this user for this questionnaire.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ensure a user has at most one membership row per questionnaire
        unique_together = ("questionnaire", "user")
        ordering = ("-created_at",)

    def __str__(self):
        # avoid referring to a non-existing role field; show a concise summary
        return f"{self.user} member for {self.questionnaire}"


class QuestionnaireSerialiser(JsonSchemaSerialiserMixin, serializers.ModelSerializer):
    """Serializer for the Questionnaire model.
    nb: putting this into serialisers.py will cause circular import issue
    because the schema.py imports serialisers.py.
    """

    class Meta:
        model = Questionnaire
        fields = ("slug", "version", "name", "description", "created_at", "document")
        # All fields are read-only by default (see `.get_fields()` method).
        read_only_fields = fields

    def validate_document(self, value):
        schema = get_questionnaire_schema()

        # Validate and return with the JSON schema
        return self._validate_document(value, schema)
