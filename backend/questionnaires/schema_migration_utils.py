"""Validation utilities for schema migrations.

Provides functions to validate that schema transforms produce structurally
valid output against frozen schema definitions passed from migration files.
"""

from typing import Tuple

from api.serialisers import JsonSchemaSerialiserMixin
from django.db.models import Count
from jsonschema import ValidationError
from rest_framework import serializers

from questionnaires.models import Questionnaire


def validate_transform(
    doc: dict,
    from_version: str,
    to_version: str,
    from_schema: dict,
    to_schema: dict,
) -> Tuple[bool, list[str]]:
    """Validate that a document transforms correctly between versions.
    
    Uses frozen schema definitions passed from migration files, ensuring
    validation is consistent regardless of current schema evolution.
    
    Args:
        doc: The document (questionnaire) to validate.
        from_version: Source schema version (before transform).
        to_version: Target schema version (after transform).
        from_schema: Frozen schema dict for from_version (from migration).
        to_schema: Frozen schema dict for to_version (from migration).
    
    Returns:
        Tuple of (is_valid, errors):
        - is_valid: True if document passes schema validation for to_version.
        - errors: List of validation error messages (empty if valid).
    
    Notes:
        - Validates against passed schemas, not current get_questionnaire_schema().
        - This ensures migrations remain valid even when current schema evolves.
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
    
    # Validate structure against target schema (frozen from migration)
    try:
        validator = JsonSchemaSerialiserMixin()
        validator._validate_document(doc, to_schema)
    except ValidationError as e:
        # jsonschema.ValidationError: validation against JSON Schema failed
        errors.append(f"JSON Schema validation failed: {e.message}")
    except serializers.ValidationError as e:
        # DRF ValidationError: version mismatch or other DRF-level validation
        error_msg = e.detail[0] if hasattr(e, 'detail') and e.detail else str(e)
        errors.append(f"Validation error: {error_msg}")
    
    return len(errors) == 0, errors


def get_db_schema_version() -> str | None:
    """Find the most common schema_version across questionnaires in database.
    
    Queries the database and returns the schema version that appears most
    frequently. Used to detect current migration state.
    
    Returns:
        - Most common schema_version string (e.g., "1" or "2025.07-1")
        - None if database is empty
    
    Notes:
        - Returns majority version (useful for detecting mixed-state issues).
        - Called by management commands to check precondition before migration.
    """
    versions = (
        Questionnaire.objects
        .values('document__schema_version')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    if not versions:
        return None
    
    return versions[0]['document__schema_version']
