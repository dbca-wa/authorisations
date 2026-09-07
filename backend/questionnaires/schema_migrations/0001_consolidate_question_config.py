"""Migration 0001: Consolidate question configuration into nested config object.

This migration transforms question definitions from a flat structure with scattered
configuration fields into a clean nested structure where all type-specific configuration
is consolidated under a single "config" object.

Forward transform (v0 → v1):
    Flat question fields (select_options, grid_columns, grid_max_rows, dependent_step,
    file_max_attachments) are moved into a nested "config" object.
    
Backward transform (v1 → v0):
    The nested "config" object is expanded back to flat question fields.

Rationale:
    - Improves schema clarity: core metadata (label, type, required) separated from
      type-specific configuration
    - Reduces API verbosity: configuration grouped logically
    - Enables scalability: new type-specific fields can be added to config without
      bloating the question definition

Usage:
    python manage.py schema_migrate --target questionnaires 1
    python manage.py schema_rollback --target questionnaires 0001 --run-id <run_id>
"""

from copy import deepcopy


def previous_schema():
    """Return the schema structure for version 0 (flat question configuration).
    
    Hard-coded schema snapshot of v0: flat configuration fields at question level.
    This matches the baseline state before consolidation.
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


def target_schema():
    """Return the schema structure for version 1 (nested config object).
    
    Hard-coded schema snapshot of v1: question configuration consolidated into
    a nested "config" object. All type-specific fields (select_options, grid_columns,
    grid_max_rows, dependent_step, file_max_attachments) are now under config.
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
                    "config": {
                        "type": "object",
                        "properties": {
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
                        "additionalProperties": False,
                        "title": "Question configuration",
                    },
                },
                "required": ["label", "type"],
            },
        },
    }


def migrate_forward(doc: dict) -> dict:
    """Transform document from schema v0 (flat config) to v1 (nested config).
    
    Consolidates scattered question configuration fields into a nested "config" object.
    Iterates through all steps/sections/questions and moves type-specific configuration
    (select_options, grid_columns, grid_max_rows, dependent_step, file_max_attachments)
    from flat question properties into a nested config object.
    
    Precondition: document.schema_version is 0 (flat structure).
    Postcondition: document.schema_version is 1 (nested structure).
    
    Args:
        doc: Questionnaire document at schema version 0
    
    Returns:
        Transformed document with schema_version = 1 and config object consolidation
    
    Raises:
        TypeError: If schema_version is not 0
    """
    _CONFIG_FIELDS = {
        "select_options",
        "grid_columns",
        "grid_max_rows",
        "dependent_step",
        "file_max_attachments",
    }
    
    doc = deepcopy(doc)
    schema_version = doc.get("schema_version")
    
    if schema_version != 0:
        raise TypeError(f"Expected schema_version 0, got {schema_version}")
    
    # Iterate through all steps/sections/questions and consolidate config
    for step in doc.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                # Extract all config fields from flat question properties
                config = {}
                for field_name in _CONFIG_FIELDS:
                    if field_name in question:
                        config[field_name] = question.pop(field_name)
                
                # Only add config object if it has at least one field
                if config:
                    question["config"] = config
    
    # Update schema version
    doc["schema_version"] = 1
    
    return doc


def migrate_backward(doc: dict) -> dict:
    """Transform document from schema v1 (nested config) back to v0 (flat config).
    
    Expands the nested "config" object back to flat question properties, reversing
    the forward migration. Enables safe rollback to schema version 0 if needed.
    
    Iterates through all steps/sections/questions and moves type-specific configuration
    from the nested config object back to flat question properties.
    
    Precondition: document.schema_version is 1 (nested structure).
    Postcondition: document.schema_version is 0 (flat structure).
    
    Args:
        doc: Questionnaire document at schema version 1
    
    Returns:
        Transformed document with schema_version = 0 and config expanded to flat fields
    
    Raises:
        TypeError: If schema_version is not 1
    """
    doc = deepcopy(doc)
    schema_version = doc.get("schema_version")
    
    if schema_version != 1:
        raise TypeError(f"Expected schema_version 1, got {schema_version}")
    
    # Iterate through all steps/sections/questions and expand config
    for step in doc.get("steps", []):
        for section in step.get("sections", []):
            for question in section.get("questions", []):
                # Extract config object if present
                config = question.pop("config", None)
                
                # Expand config fields back to flat question properties
                if config and isinstance(config, dict):
                    question.update(config)
    
    # Update schema version
    doc["schema_version"] = 0
    
    return doc
