"""Sample migration 0001: Baseline transition (version 0 → 1).

A simple test migration showing the contract that framework expects.
Transforms a document from version 0 (baseline) to version 1 (first ordinal).

This migration is used by framework unit tests and does not depend on
questionnaires or any app-specific code.
"""


def previous_schema() -> dict:
    """Hard-coded schema snapshot at version 0 (baseline)."""
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
    """Hard-coded schema snapshot at version 1."""
    # Same as previous for this simple test migration
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


def migrate_forward(doc: dict) -> dict:
    """Transform document from version 0 → version 1.
    
    Simple transformation: just update schema_version.
    """
    doc["schema_version"] = 1
    return doc


def migrate_backward(doc: dict) -> dict:
    """Transform document from version 1 → version 0.
    
    Reversal: restore schema_version to 0.
    """
    doc["schema_version"] = 0
    return doc
