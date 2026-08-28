"""Migration 0001: Versioning baseline transition (0 → 1).

Transforms existing applications from legacy baseline version (0) to
ordinal versioning. This is the first official migration and establishes
version 1 as the anchor point for all future schema changes.

Note: The management command checks current DB version before running this
migration. This ensures idempotency: running the same migration twice is a
safe no-op.
"""

from copy import deepcopy


def previous_schema():
    """Return the schema structure that existed at version 0 (baseline).
    
    This is a frozen snapshot of version 0. Hard-coded to ensure it never changes,
    even if the current schema evolves. IDENTICAL to target_schema() except for
    schema_version default (0 instead of 1).
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


def target_schema():
    """Return the schema structure for version 1.
    
    Ordinal versioning introduces explicit version 1 as the baseline.
    All future changes increment from here. Schema structure is identical
    to version 0 except schema_version default is 1 instead of 0.
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
                "title": "Schema version",
                "default": 1,
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


def migrate_forward(document: dict) -> dict:
    """Transform: version 0 (unversioned) → version 1.
    
    Precondition: document.schema_version is 0 (legacy baseline).
    Management command verifies this before calling.
    """
    if document.get("schema_version") != 0:
        raise TypeError(
            f"Expected schema_version 0, but found schema_version={document.get('schema_version')}"
        )
    
    document = deepcopy(document)
    document["schema_version"] = 1
    return document


def migrate_backward(document: dict) -> dict:
    """Transform: version 1 → version 0 (rollback).
    
    Rollback support: Restores documents to version 0 state.
    """
    if document.get("schema_version") != 1:
        raise TypeError(
            f"Expected schema_version 1, got {document.get('schema_version')}"
        )
    
    document = deepcopy(document)
    document["schema_version"] = 0
    return document
