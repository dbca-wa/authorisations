from api.serialisers import JsonSchemaSerialiserMixin
from django.db import models
from processes.models import AuthorisationProcess
from rest_framework import serializers

from .bugfix import DocumentJSONField
from .schema import get_questionnaire_schema


class Questionnaire(models.Model):
    """Model to represent a questionnaire with steps, sections, and questions."""

    id = models.BigAutoField(primary_key=True)
    process = models.ForeignKey(
        AuthorisationProcess,
        related_name="questionnaires",
        on_delete=models.PROTECT,
        editable=True,
    )
    version = models.PositiveSmallIntegerField(
        default=1, blank=False, null=False, editable=False
    )
    code = models.SlugField(
        max_length=20,
        null=False,
        blank=False,
        db_index=True,
        editable=True,
        help_text="Stable questionnaire code used to identify a version lineage within a process.",
    )
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        editable=True,
        help_text='The display name of the questionnaire such as; "New application", "Renewal" etc.',
    )
    description = models.TextField(
        max_length=500, blank=False, null=False, editable=True
    )
    document = DocumentJSONField(
        schema=get_questionnaire_schema(),
        blank=False,
        null=False,
        editable=True,
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        null=False,
        blank=False,
        db_index=True,
        help_text="Controls questionnaire order within an authorisation process.",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "users.User",
        related_name="questionnaires",
        on_delete=models.PROTECT,
        editable=False,
    )
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    updated_by = models.ForeignKey(
        "users.User",
        related_name="updated_questionnaires",
        on_delete=models.PROTECT,
        editable=False,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = (
            "process_id",
            "code",
            "-version",
        )
        constraints = [
            models.UniqueConstraint(
                "process",
                "code",
                models.F("version").desc(),
                name="qnaire_unique_process_code_version_desc",
            )
        ]

    def __str__(self):
        return (
            f'Questionnaire "{self.name}" [{self.code}] '
            f'(v{self.version}) for {self.process.slug}'
        )


class QuestionnaireSerialiser(JsonSchemaSerialiserMixin, serializers.ModelSerializer):
    """Serializer for the Questionnaire model.
    nb: putting this into serialisers.py will cause circular import issue
    because the schema.py imports serialisers.py.
    """

    process_slug = serializers.SlugField(
        source="process.slug",
        required=False,
        read_only=True,
    )

    class Meta:
        model = Questionnaire
        fields = (
            "process_slug",
            "id",
            "code",
            "name",
            "version",
            "description",
            "sort_order",
            "created_at",
            "updated_at",
            "document",
        )
        # All fields are read-only by default (see `.get_fields()` method).
        read_only_fields = fields

    def validate_document(self, value):
        schema = get_questionnaire_schema()

        # Validate and return with the JSON schema
        return self._validate_document(value, schema)
