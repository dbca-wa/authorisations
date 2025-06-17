from copy import deepcopy
from drf_jsonschema_serializer import SerializerJSONField, to_jsonschema
from drf_jsonschema_serializer.convert import converter
from frozendict import frozendict
from jsonschema import Draft202012Validator
from rest_framework import serializers


class ReferenceField(serializers.Field):
    """
    A custom field to handle references in the JSON Schema.
    This is a placeholder for future reference handling.
    """

    def __init__(self, definition: str, *args, **kwargs):
        self.definition = definition
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        print(f"Converting value to representation: {value}")
        return value

    def to_internal_value(self, data):
        return data


@converter
class ReferenceFieldConverter:
    field_class = ReferenceField

    def convert(self, field):
        return {"$ref": f"#/$defs/{field.definition}"}


QUESTION_TYPE_CHOICES = [
    ("text", "Text"),
    ("textarea", "Textarea Multi-line"),
    ("number", "Numeric"),
    ("checkbox", "Checkbox"),
    ("select", "Multiple Choice Select"),
    ("date", "Date"),
    # ("grid", "Grid (Matrix of options)"),
]


#  Grid question column definition
class GridQuestionColumnSerialiser(serializers.Serializer):
    label = serializers.CharField(max_length=255, required=True)
    type = serializers.ChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        required=True,
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    select_options = serializers.ListField(
        child=serializers.CharField(max_length=50, allow_blank=True),
        max_length=50,
        required=False,
        allow_empty=False,
        allow_null=True,
    )


class QuestionSerialiser(serializers.Serializer):
    label = serializers.CharField(max_length=500, required=True)
    type = serializers.ChoiceField(
        choices=QUESTION_TYPE_CHOICES + [("grid", "Grid (Matrix of options)")],
        required=True,
    )
    is_required = serializers.BooleanField(
        default=False, required=False, allow_null=False
    )
    description = serializers.CharField(
        max_length=1000, required=False, allow_null=False, allow_blank=True
    )
    select_options = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=50,
        required=False,
        allow_null=True,
        allow_empty=False,
    )
    grid_columns = serializers.ListField(
        child=SerializerJSONField(GridQuestionColumnSerialiser),
        max_length=10,
        required=False,
        allow_null=True,
        allow_empty=False,
    )
    grid_max_rows = serializers.IntegerField(
        min_value=1,
        max_value=20,
        # default=10,
        required=False,
        allow_null=True,
        # allow_empty=True,
    )


# TODO: How do we store the answers?
# class QuestionnaireGridQuestion(QuestionnaireQuestion):
#     value = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     values = serializers.ListField(
#         child=serializers.ListField(
#             child=serializers.CharField(max_length=255, allow_blank=True),
#             allow_empty=True,
#         ),
#         max_length=10,
#         required=False,
#         allow_empty=True,
#     )


class SectionSerialiser(serializers.Serializer):
    title = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(
        max_length=3000, required=False, allow_blank=True
    )
    questions = serializers.ListField(
        # child=SerializerJSONField(QuestionSerialiser),
        child=ReferenceField("question"),
        required=True,
        allow_empty=False,
        min_length=1,
    )


class StepSerialiser(serializers.Serializer):
    title = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    sections = serializers.ListField(
        # child=SerializerJSONField(SectionSerialiser),
        child=ReferenceField("section"),
        required=True,
        allow_empty=False,
        min_length=1,
    )


# This should never be modified, therefore we use frozendict
# (and django-jsonform does modify it when passed as a field construct param)
_SCHEMA_QUESTIONNAIRE: frozendict = frozendict(
    {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "JSON Schema definition for a questionnaire with steps, sections, and questions.",
        "title": "Questionnaire Schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "type": "string",
                "title": "Schema version",
                "default": "2025.06-1",  # Current version of the schema
                "readOnly": True,
                "description": "The version of the questionnaire schema.",
            },
            "steps": {
                "title": "Steps",
                "type": "array",
                "items": {"$ref": "#/$defs/step"},
                "minItems": 1,
            },
        },
        "$defs": {
            "step": to_jsonschema(StepSerialiser()),
            "section": to_jsonschema(SectionSerialiser()),
            "question": to_jsonschema(QuestionSerialiser()),
        },
    }
)


def get_schema() -> dict:
    """Always return a deepcopy of the schema to avoid modifications
    to the original schema (yes, django-jsonform does that).

    TODO: Implement schema versioning in the future.
    """
    schema: dict = deepcopy(dict(_SCHEMA_QUESTIONNAIRE))
    schema["properties"]["schema_version"]["default"] = "2025.06-1"
    return schema


# Do check the schema validation at the startup
Draft202012Validator.check_schema(get_schema())
