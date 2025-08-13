from copy import deepcopy

from drf_jsonschema_serializer import to_jsonschema
from frozendict import frozendict
from jsonschema.validators import Draft202012Validator

from .serialisers import QuestionSerialiser, SectionSerialiser, StepSerialiser

# This should never be modified on runtime, therefore we use frozendict
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
                "default": "2025.07-1",  # Current version of the schema
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
        "required": ["schema_version", "steps"],
        "additionalProperties": False,
        "$defs": {
            "step": to_jsonschema(StepSerialiser()),
            "section": to_jsonschema(SectionSerialiser()),
            "question": to_jsonschema(QuestionSerialiser()),
        },
    }
)


def get_questionnaire_schema() -> dict:
    """Always return a deepcopy of the schema to avoid modifications
    to the original schema (yes, django-jsonform does that).

    TODO: Implement schema versioning in the future.
    """
    schema: dict = deepcopy(dict(_SCHEMA_QUESTIONNAIRE))
    schema["properties"]["schema_version"]["default"] = "2025.07-1"
    return schema


# Do check the schema validation at the startup
Draft202012Validator.check_schema(get_questionnaire_schema())
