from drf_jsonschema_serializer import SerializerJSONField
from drf_jsonschema_serializer.convert import converter
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

    # def to_internal_value(self, data):
    #     return data


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
    # ("file", "File Upload"),
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
        choices=QUESTION_TYPE_CHOICES
        + [("file", "File Upload"), ("grid", "Grid (Matrix of options)")],
        required=True,
    )
    # Getting validation error; "None is not of type 'boolean'"
    # while creating a new questionnaire
    is_required = serializers.BooleanField(
        default=False, required=False, allow_null=False
    )
    description = serializers.CharField(
        max_length=1000, required=False, allow_null=False, allow_blank=True
    )
    select_options = serializers.ListField(
        child=serializers.CharField(max_length=100),
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
