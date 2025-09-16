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
        "additionalProperties": False,
        "required": ["schema_version", "active_step", "steps"],
        "properties": {
            "schema_version": {
                "type": "string",
                "title": "Schema version",
                "default": "2025.09-1",  # Current version of the schema
                "readOnly": True,
                "description": "The version of the application answers schema.",
            },
            "active_step": {
                "type": "integer",
                "title": "Active step",
                "minimum": 0,
            },
            "steps": {
                "title": "Step States",
                "type": "array",
                "items": {"$ref": "#/$defs/step_state"},
                "minItems": 1,
            },
        },
        # Additional definitions for complex types
        "$defs": {
            # The state for a step and its answers
            "step_state": {
                "type": "object",
                "title": "Step State",
                "additionalProperties": False,
                "required": ["is_valid", "answers"],
                "properties": {
                    "is_valid": {"type": ["boolean", "null"], "default": None},
                    "answers": {"$ref": "#/$defs/answers"},
                },
            },
            # Answers for the whole step (all sections)
            "answers": {
                "type": "object",
                "title": "Answers",
                "additionalProperties": False,
                "properties": {},
                "patternProperties": {
                    # The regex matches the answer key format
                    # e.g. [section]-[question]
                    r"^\d+\-\d+$": {
                        # Primitive type or a grid question answer
                        "oneOf": _PRIMITIVE_TYPES + [{"$ref": "#/$defs/grid_answer"}],
                    },
                },
            },
            # An answer to a grid question is an array of objects
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
    # schema["properties"]["schema_version"]["default"] = "2025.09-1"
    return schema


# Do check the schema validation at the startup
Draft202012Validator.check_schema(get_answers_schema())
