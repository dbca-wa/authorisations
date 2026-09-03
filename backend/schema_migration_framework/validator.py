"""Schema validation for migration transforms.

Validates that transformed documents conform to target schema definitions.
Uses jsonschema for JSON Schema validation (no DRF or app-specific integrations).
"""

from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError
from typing import Tuple


def validate_transform(
    doc: dict,
    from_version: int | str,
    to_version: int | str,
    to_schema: dict,
) -> Tuple[bool, list[str]]:
    """Validate that a transformed document conforms to target schema.
    
    Uses frozen schema definition passed from migration file, ensuring validation
    is consistent regardless of current schema evolution.
    
    Args:
        doc: The document to validate (after transformation).
        from_version: Source schema version (before transform) - for reference only.
        to_version: Target schema version (after transform).
        to_schema: Frozen schema dict for to_version (from migration file).
                   Must be a valid JSON Schema.
    
    Returns:
        Tuple of (is_valid, errors):
        - is_valid: True if document passes schema validation.
        - errors: List of validation error messages (empty if valid).
    
    Notes:
        - Validates against passed schema, not from current application code.
        - This ensures migrations remain valid even when schema evolves.
        - Assumes document has already been transformed by migration.
    """
    if not isinstance(doc, dict):
        return False, ["Document must be a dict"]
    
    errors = []
    
    # Check schema_version matches expected target
    doc_version = doc.get("schema_version")
    if doc_version != to_version:
        errors.append(
            f"Expected schema_version {to_version}, got {doc_version}"
        )
    
    # Validate structure against target schema using jsonschema
    try:
        validator = Draft202012Validator(to_schema)
        validation_errors = list(validator.iter_errors(doc))
        
        if validation_errors:
            for error in validation_errors:
                # Build readable error message with path to failing key
                path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                errors.append(f"Validation failed at {path}: {error.message}")
    except JsonSchemaValidationError as e:
        errors.append(f"JSON Schema validation error: {e.message}")
    except Exception as e:
        errors.append(f"Unexpected validation error: {str(e)}")
    
    return len(errors) == 0, errors
