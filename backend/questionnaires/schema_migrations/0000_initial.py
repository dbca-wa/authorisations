"""Migration 0000: Bridge from calendar to ordinal versioning.

Forward-only migration that transforms calendar versioning ("2025.07-1")
to ordinal versioning (0, 1, 2, ...).

Usage:
    python manage.py schema_migrate --target questionnaires 0001
    Transforms "2025.07-1" → version 0 → version 1

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
                "default": 0,
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
                    "title": {
                        "type": "string",
                        "maxLength": 100,
                        "minLength": 1,
                        "title": "Title",
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 100,
                        "title": "Description",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/section"},
                        "minItems": 1,
                        "title": "Sections",
                    },
                },
                "required": ["title", "sections"],
            },
            "section": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 100,
                        "minLength": 1,
                        "title": "Title",
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 3000,
                        "title": "Description",
                    },
                    "questions": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/question"},
                        "minItems": 1,
                        "title": "Questions",
                    },
                },
                "required": ["title", "questions"],
            },
            "question": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "maxLength": 500,
                        "minLength": 1,
                        "title": "Label",
                    },
                    "type": {
                        "type": "string",
                        "enum": [
                            "text",
                            "textarea",
                            "number",
                            "checkbox",
                            "select",
                            "date",
                            "file",
                            "grid",
                        ],
                        "enumNames": [
                            "Text",
                            "Textarea Multi-line",
                            "Numeric",
                            "Checkbox",
                            "Multiple Choice Select",
                            "Date",
                            "File Upload",
                            "Grid (Matrix of options)",
                        ],
                        "title": "Type",
                    },
                    "is_required": {
                        "type": "boolean",
                        "title": "Is required",
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 1000,
                        "title": "Description",
                    },
                    "select_options": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "maxLength": 100,
                            "minLength": 1,
                        },
                        "maxItems": 50,
                        "title": "Select options",
                    },
                    "grid_columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "maxLength": 255,
                                    "minLength": 1,
                                    "title": "Label",
                                },
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "text",
                                        "textarea",
                                        "number",
                                        "checkbox",
                                        "select",
                                        "date",
                                    ],
                                    "enumNames": [
                                        "Text",
                                        "Textarea Multi-line",
                                        "Numeric",
                                        "Checkbox",
                                        "Multiple Choice Select",
                                        "Date",
                                    ],
                                    "title": "Type",
                                },
                                "description": {
                                    "type": "string",
                                    "maxLength": 255,
                                    "title": "Description",
                                },
                                "select_options": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "maxLength": 50,
                                    },
                                    "maxItems": 50,
                                    "title": "Select options",
                                },
                            },
                            "required": ["label", "type"],
                        },
                        "maxItems": 10,
                        "title": "Grid columns",
                    },
                    "grid_max_rows": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                        "maximum": 20,
                        "title": "Grid max rows",
                    },
                    "dependent_step": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                        "maximum": 10,
                        "title": "Dependent step",
                    },
                    "file_max_attachments": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                        "maximum": 20,
                        "title": "File max attachments",
                    },
                },
                "required": ["label", "type"],
            },
        },
    }


def migrate_forward(doc: dict) -> dict:
    """Transform: calendar version ("2025.07-1") → version 0 (ordinal).
    
    Precondition: document.schema_version is "2025.07-1" (calendar).
    This migration bridges from legacy calendar versioning to ordinal baseline.
    
    Args:
        doc: Questionnaire document at calendar version
    
    Returns:
        Transformed document with schema_version = 0
    
    Raises:
        TypeError: If precondition not met (schema_version != "2025.07-1").
    """
    _CALENDAR_VERSION = "2025.07-1"
    
    if doc.get("schema_version") != _CALENDAR_VERSION:
        raise TypeError(
            f"Expected schema_version '{_CALENDAR_VERSION}', got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = 0
    return doc



