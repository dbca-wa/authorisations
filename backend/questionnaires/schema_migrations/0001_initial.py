"""Migration 0001: Versioning baseline transition (0 → 1).

Transforms existing questionnaires from legacy baseline version (0) to
ordinal versioning. This is the first official migration and establishes
version 1 as the anchor point for all future schema changes.

Note: The management command checks current DB version before running this
migration. This ensures idempotency: running the same migration twice is a
safe no-op.
"""

from copy import deepcopy


def previous_schema():
    """Return the schema structure that existed at version 2025.07-1.
    
    This is a frozen snapshot of the schema at 2025.07-1. Hard-coded to ensure
    it never changes, even if the current schema evolves. Future migrations
    reference this to understand the previous schema state.
    """
    return {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "JSON Schema definition for a questionnaire with steps, sections, and questions.",
        "title": "Questionnaire Schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "type": "string",
                "title": "Schema version",
                "default": "2025.07-1",
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
            "step": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/section"},
                    },
                },
                "required": ["title", "description", "sections"],
                "additionalProperties": False,
            },
            "section": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/question"},
                    },
                },
                "required": ["title", "description", "questions"],
                "additionalProperties": False,
            },
            "question": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "type": {"type": "string"},
                    "is_required": {"type": "boolean"},
                    "description": {"type": "string"},
                },
                "required": ["label", "type", "is_required", "description"],
                "additionalProperties": False,
            },
        },
    }


def target_schema():
    """Return the schema structure for version 1 (the target of this migration).
    
    This is a frozen snapshot of version 1. Hard-coded to ensure migrations
    forever validate against the same target schema, regardless of future
    schema evolution.
    """
    return {
        "$id": "https://example.com/arrays.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "JSON Schema definition for a questionnaire with steps, sections, and questions.",
        "title": "Questionnaire Schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "type": "integer",
                "minimum": 0,
                "title": "Schema version",
                "default": 1,
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
            "step": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/section"},
                    },
                },
                "required": ["title", "description", "sections"],
                "additionalProperties": False,
            },
            "section": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/question"},
                    },
                },
                "required": ["title", "description", "questions"],
                "additionalProperties": False,
            },
            "question": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "type": {"type": "string"},
                    "is_required": {"type": "boolean"},
                    "description": {"type": "string"},
                },
                "required": ["label", "type", "is_required", "description"],
                "additionalProperties": False,
            },
        },
    }


def migrate_forward(doc: dict) -> dict:
    """Transform: baseline version (0) → ordinal versioning (1).
    
    Precondition: This function is called only when document.schema_version == 0.
    The management command verifies this before calling migrate_forward().
    
    Args:
        doc: Questionnaire document with schema_version = 0
    
    Returns:
        Transformed document with schema_version = 1
    
    Raises:
        TypeError: If precondition not met (defensive check).
    """
    if doc.get("schema_version") != 0:
        raise TypeError(
            f"Expected schema_version 0, got {doc.get('schema_version')}"
        )

    doc = deepcopy(doc)
    doc["schema_version"] = 1
    return doc


def migrate_backward(doc: dict) -> dict:
    """Transform: ordinal versioning (1) → baseline version (0).
    
    Rollback support: restores documents to pre-migration state.
    
    Args:
        doc: Questionnaire document with schema_version = 1
    
    Returns:
        Transformed document with schema_version = 0
    
    Raises:
        TypeError: If precondition not met (defensive check).
    """
    if doc.get("schema_version") != 1:
        raise TypeError(
            f"Expected schema_version 1, got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = 0
    return doc
