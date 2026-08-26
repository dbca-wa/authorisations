"""Sample migration 0002: Add description field (version 1 → 2).

Test migration showing schema evolution: adding a new optional field.

Used by framework unit tests and does not depend on questionnaires.
"""


def previous_schema() -> dict:
    """Hard-coded schema snapshot at version 1."""
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer"},
            "name": {"type": "string"},
            "items": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["schema_version", "name"]
    }


def target_schema() -> dict:
    """Hard-coded schema snapshot at version 2 (with new description field)."""
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer"},
            "name": {"type": "string"},
            "description": {"type": ["string", "null"]},
            "items": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["schema_version", "name"]
    }


def migrate_forward(doc: dict) -> dict:
    """Transform document from version 1 → version 2.
    
    Adds description field with null default.
    """
    doc["schema_version"] = 2
    doc["description"] = None
    return doc


def migrate_backward(doc: dict) -> dict:
    """Transform document from version 2 → version 1.
    
    Removes description field and restores version.
    """
    doc.pop("description", None)
    doc["schema_version"] = 1
    return doc
