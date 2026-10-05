"""Migration 0000: Bridge from calendar to ordinal versioning.

Forward-only migration that transforms calendar versioning ("2025.09-1")
to ordinal versioning (0, 1, 2, ...).

Usage:
    python manage.py schema_migrate --target applications 0001
    Transforms "2025.09-1" → version 0 → version 1

Note: This migration handles forward transformation only. Once at ordinal
versioning (v0+), you cannot rollback to calendar versions. Calendar versions
are pre-migration baseline states, not outputs of the versioning system.

This eliminates the need for the separate schema_zero command.
"""

from copy import deepcopy


def target_schema():
    """Return the schema structure for version 0 (integer baseline).
    
    Hard-coded schema snapshot matching the v0 baseline state.
    """
    _PRIMITIVE_TYPES = [
        {"type": "string"},
        {"type": "integer", "minimum": 0},
        {"type": "boolean"},
        {"type": "null"},
    ]

    return {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "JSON Schema definition for an application answers to a questionnaire.",
        "title": "Application Answers Schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "active_step", "steps"],
        "properties": {
            "schema_version": {
                "type": "integer",
                "minimum": 0,
                "title": "Schema version",
                "default": 0,
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
        "$defs": {
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
            "answers": {
                "type": "object",
                "title": "Answers",
                "additionalProperties": False,
                "properties": {},
                "patternProperties": {
                    r"^\d+\-\d+$": {
                        "oneOf": [
                            *_PRIMITIVE_TYPES,
                            {"$ref": "#/$defs/grid_answer"},
                            {"$ref": "#/$defs/file_attachments"},
                        ],
                    },
                },
            },
            "grid_answer": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": {"oneOf": _PRIMITIVE_TYPES},
                },
            },
            "file_attachments": {
                "type": "array",
                "items": {"type": "string", "format": "uuid"},
                "minItems": 1,
                "maxItems": 20,
            },
        },
    }


def migrate_forward(doc: dict) -> dict:
    """Transform: calendar version ("2025.09-1") → version 0 (ordinal).
    
    Precondition: document.schema_version is "2025.09-1" (calendar).
    This migration bridges from legacy calendar versioning to ordinal baseline.
    
    Args:
        doc: Application document at calendar version
    
    Returns:
        Transformed document with schema_version = 0
    
    Raises:
        TypeError: If precondition not met (schema_version != "2025.09-1").
    """
    _CALENDAR_VERSION = "2025.09-1"

    doc = deepcopy(doc)
    schema_version = doc.get("schema_version")

    # migrate from legacy calendar versioning to ordinal baseline
    if schema_version == _CALENDAR_VERSION:
        doc["schema_version"] = schema_version = 0

    # just make sure we are running for document's version 0, otherwise raise an error
    if schema_version != 0:
        raise TypeError(
            f"Expected schema_version '0', got {schema_version}"
        )

    return doc




