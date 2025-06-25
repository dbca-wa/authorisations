from django.db import models
from django.urls import reverse
from django_jsonform.models.fields import JSONField
from rest_framework import serializers

from questionnaire.serialisers import get_schema


class Questionnaire(models.Model):
    slug = models.SlugField(
        max_length=20, null=False, blank=False, unique=False, db_index=False
    )
    version = models.PositiveSmallIntegerField(default=1, blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    document = JSONField(
        schema=get_schema(),
        blank=False,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "auth.User",
        related_name="questionnaires",
        on_delete=models.PROTECT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "slug",
                models.F("version").desc(),
                name="unique_slug_version_desc",
                include=["name"],
            )
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    @property
    def serialised(self):
        """Return the serialised version of the questionnaire."""
        return QuestionnaireSerialiser(self).data

    def get_absolute_url(self):
        return reverse("questionnaire", kwargs={"slug": self.slug})


class QuestionnaireSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = ("slug", "version", "name", "document")


# class Application(models.Model):
#     questionnaire = models.ForeignKey(
#         Questionnaire,
#         related_name="applications",
#         on_delete=models.PROTECT,
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     # answers =

#     # def __str__(self):
#     #     # return f"ApplicationForm(slug={self.slug})"
#     #     return self.questionnaire.get("name", "Unnamed application form")


# class FormStep(models.Model):
#     application = models.ForeignKey(
#         ApplicationForm, related_name='steps', on_delete=models.CASCADE)
#     title = models.CharField(max_length=50)
#     short_description = models.CharField(max_length=255)


# class FormSection(models.Model):
#     step = models.ForeignKey(
#         FormStep, related_name='sections', on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)


# class FormQuestionType(models.TextChoices):
#     TEXT = 'text', 'Text'
#     TEXTAREA = 'textarea', 'Textarea Multi-line'
#     CHECKBOX = 'checkbox', 'Checkbox'
#     SELECT = 'select', 'Multiple Choice Select'
#     DATE = 'date', 'Date'
#     GRID = 'grid', 'Grid (Matrix of options)'

# class FormQuestion(models.Model):
#     section = models.ForeignKey(
#         FormSection, related_name='questions', on_delete=models.CASCADE)
#     label = models.CharField(max_length=50)
#     type = models.CharField(max_length=50, choices=FormQuestionType)
#     is_required = models.BooleanField(default=False)
#     value = models.CharField(max_length=255, blank=True, null=True)
#     options = pg_fields.ArrayField(
#         models.CharField(max_length=50, blank=True),
#         size=100, blank=True, null=True,
#     )
#     description = models.TextField(blank=True, null=True)
#     order = models.IntegerField(default=0)

#     class Meta:
#         ordering = ['order']  # Ensure questions are ordered by 'order' field
