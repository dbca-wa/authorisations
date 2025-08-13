from django.db import models
from django.urls import reverse
from django_jsonform.models.fields import JSONField
from rest_framework import serializers

from .schema import get_questionnaire_schema


class Questionnaire(models.Model):
    """Model to represent a questionnaire with steps, sections, and questions."""

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(
        max_length=20, null=False, blank=False, unique=False, db_index=False, editable=True,
    )
    version = models.PositiveSmallIntegerField(default=1, blank=False, null=False, editable=False)
    name = models.CharField(max_length=100, blank=False, null=False, editable=True)
    description = models.TextField(max_length=500, blank=False, null=False, editable=True)
    document = JSONField(
        schema=get_questionnaire_schema(),
        blank=False,
        null=False,
        editable=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        "auth.User",
        related_name="questionnaires",
        on_delete=models.PROTECT,
        editable=False,
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

    # def get_absolute_url(self):
    #     return reverse("questionnaire", kwargs={"slug": self.slug})


class QuestionnaireSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = ("slug", "version", "name", "description", "created_at", "document")
