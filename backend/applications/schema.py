from copy import deepcopy

from frozendict import frozendict
from jsonschema import Draft202012Validator

_PRIMITIVE_TYPES = [
    {"type": "string"},
    {"type": "integer", "minimum": 0},
    {"type": "boolean"},
    {"type": "null"},
]


# This should never be modified on runtime, therefore we use frozendict
# (and django-jsonform does modify it when passed as a field construct param)
_SCHEMA_ANSWERS: frozendict = frozendict(
    {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "JSON Schema definition for an application answers to a questionnaire.",
        "title": "Application Answers Schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "type": "string",
                "title": "Schema version",
                "default": "2025.07-1",  # Current version of the schema
                "readOnly": True,
                "description": "The version of the application answers schema.",
            },
            "answers": {
                "title": "Answers",
                "type": "object",
                "properties": {},
                "patternProperties": {
                    # The regex matches the answer key format
                    # e.g. [step]-[section]-[question]
                    "^\d+\-\d+\-\d+$": {
                        # Primitive type or a grid question answer
                        "oneOf": _PRIMITIVE_TYPES + [{"$ref": "#/$defs/grid_answer"}],
                    },
                },
            },
        },
        "required": ["schema_version", "answers"],
        "additionalProperties": False,
        "$defs": {
            "grid_answer": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": {"oneOf": _PRIMITIVE_TYPES},
                },
            },
        },
    }
)


def get_answers_schema() -> dict:
    """Always return a deepcopy of the schema to avoid modifications
    to the original schema (yes, django-jsonform does that).

    TODO: Implement schema versioning in the future.
    """
    schema: dict = deepcopy(dict(_SCHEMA_ANSWERS))
    # schema["properties"]["schema_version"]["default"] = "2025.07-1"
    return schema


# Do check the schema validation at the startup
Draft202012Validator.check_schema(get_answers_schema())
