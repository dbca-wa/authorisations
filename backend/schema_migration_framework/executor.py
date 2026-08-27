"""Migration execution with transaction safety and per-record error handling.

Orchestrates applying migrations to model records within atomic transactions.
Provides helpers for validation testing, transform application, and error reporting.
"""

from copy import deepcopy
from typing import Any, Callable
import importlib

from django.apps import apps
from django.db import transaction


def get_db_schema_version(records: list[Any], version_accessor: Callable[[Any], Any]) -> int | None:
    """Get the current schema version from records in the database.
    
    ALL records must be at the same schema version. If records contain different
    versions, raises an exception. This is a consistency requirement: migrations
    only work on uniform database states.
    
    Args:
        records: List of model instances with documents (e.g., Questionnaire objects).
        version_accessor: Callable that takes a record and returns its schema version.
                         Example: lambda q: q.document.get("schema_version")
    
    Returns:
        - Schema version as unsigned integer (e.g., 0, 1, 2) if all records match
        - None if records list is empty
    
    Raises:
        RuntimeError: If records contain different schema versions.
                     Indicates failed or partial migration requiring manual recovery.
        TypeError: If any schema_version value is not an integer.
    
    Notes:
        - Does NOT use majority voting. All records must be at same version.
        - Called before migration to verify precondition.
        - If this raises RuntimeError, indicates inconsistent database state.
        - All schema_version values must be unsigned integers; no silent conversions.
    """
    if not records:
        return None
    
    version_counts = {}
    
    for record in records:
        raw_version = version_accessor(record)
        
        # Enforce that all versions are integers; no silent conversions
        if not isinstance(raw_version, int):
            raise TypeError(
                f"Expected schema_version to be integer, got {type(raw_version).__name__}: {raw_version!r}"
            )
        
        version_counts[raw_version] = version_counts.get(raw_version, 0) + 1
    
    # If more than one version exists, database is in inconsistent state
    if len(version_counts) > 1:
        raise RuntimeError(
            f"Database contains records at multiple schema versions: {version_counts}.\n"
            f"This indicates a failed or partial migration. All records must be at "
            f"the same version before proceeding."
        )
    
    # Single version: return it
    return next(iter(version_counts)) if version_counts else None


def validate_all_transforms(
    records: list[Any],
    migration: Any,
    from_version: int | str,
    to_version: int | str,
    doc_getter: Callable[[Any], dict],
    validate_fn: Callable[[dict, int | str, int | str, dict], tuple[bool, list[str]]],
) -> tuple[int, list[tuple[Any, str]]]:
    """Validate all transforms before applying them.
    
    Args:
        records: List of model instances to transform.
        migration: Migration module with previous_schema(), target_schema(), migrate_forward().
        from_version: Current schema version before transform.
        to_version: Target schema version after transform.
        doc_getter: Callable to extract document from record (e.g., lambda q: q.document).
        validate_fn: Validation function (validate_transform from validator.py).
    
    Returns:
        Tuple of (success_count, failed_records):
        - success_count: Number of records that passed validation
        - failed_records: List of (record, error_message) tuples for failed records
    
    Notes:
        - Does NOT modify records.
        - Uses deepcopy to test transforms on copies, leaving originals untouched.
    """
    to_schema = migration.target_schema()
    success_count = 0
    failed_records = []
    
    for record in records:
        doc = doc_getter(record)
        
        # Test the transform on a copy
        try:
            transformed = deepcopy(doc)
            transformed = migration.migrate_forward(transformed)
            
            # Validate transformed document
            is_valid, errors = validate_fn(transformed, from_version, to_version, to_schema)
            
            if not is_valid:
                error_msg = f"Validation failed: {', '.join(errors)}"
                failed_records.append((record, error_msg))
            else:
                success_count += 1
        except Exception as e:
            failed_records.append((record, str(e)))
    
    return success_count, failed_records


def apply_transforms(
    records: list[Any],
    migration: Any,
    doc_getter: Callable[[Any], dict],
    doc_setter: Callable[[Any, dict], None],
    save_fn: Callable[[Any], None],
) -> None:
    """Apply migration transforms to records (called within atomic transaction).
    
    Args:
        records: List of model instances to transform.
        migration: Migration module with migrate_forward().
        doc_getter: Callable to extract document from record (e.g., lambda q: q.document).
        doc_setter: Callable to set transformed document on record (e.g., lambda q, d: setattr(q, 'document', d)).
        save_fn: Callable to save record (e.g., lambda q: q.save(update_fields=["document"])).
    
    Notes:
        - Should be called within transaction.atomic() context.
        - Modifies records in-place and saves them.
    """
    for record in records:
        doc = doc_getter(record)
        transformed = migration.migrate_forward(doc)
        doc_setter(record, transformed)
        save_fn(record)


def execute_atomic_transaction(operation: Callable[[], None]) -> None:
    """Execute an operation within an atomic database transaction.
    
    Args:
        operation: Callable that performs database operations.
    
    Raises:
        Exception: If operation raises any exception (transaction is rolled back).
    
    Notes:
        - All database changes are committed atomically or rolled back entirely.
        - Any exception inside operation causes full rollback.
    """
    with transaction.atomic():
        operation()


def get_target_model(target: dict[str, str]) -> type:
    """Dynamically load Django model from target registry entry.
    
    Args:
        target: Target configuration dict with 'model' key (e.g., "questionnaires.Questionnaire").
    
    Returns:
        Django model class.
    
    Raises:
        LookupError: If app_label or model_name not found.
        ValueError: If model format is invalid.
    """
    model_path = target["model"]
    
    if "." not in model_path:
        raise ValueError(
            f"Invalid model format: {model_path!r}. Expected 'app_label.ModelName'."
        )
    
    app_label, model_name = model_path.rsplit(".", 1)
    return apps.get_model(app_label, model_name)


def get_schema_version_from_document(document: dict, version_path: str) -> int | None:
    """Extract schema version from document using dot-notation path.
    
    Supports nested paths like "metadata.schema.version" by traversing dot-separated keys.
    
    Args:
        document: JSON document dict.
        version_path: Path to version field using dot notation (e.g., "schema_version" or "metadata.version").
    
    Returns:
        Schema version value if found, None if path doesn't exist.
    
    Raises:
        TypeError: If traversal encounters non-dict intermediate value (path invalid for document structure).
    """
    parts = version_path.split(".")
    current = document
    
    for i, part in enumerate(parts):
        if not isinstance(current, dict):
            raise TypeError(
                f"Cannot traverse version_path {version_path!r}: "
                f"part '{'.'.join(parts[:i])}' is not a dict, got {type(current).__name__}"
            )
        
        current = current.get(part)
        
        # If intermediate part doesn't exist, return None (allows optional nested fields)
        if current is None:
            return None
    
    return current


def get_migrations_package_path(migrations_package: str) -> str:
    """Convert dotted package path to filesystem path.
    
    Args:
        migrations_package: Dotted import path (e.g., "questionnaires.schema_migrations").
    
    Returns:
        Filesystem path to package directory.
    
    Raises:
        ModuleNotFoundError: If package cannot be imported.
        AttributeError: If package doesn't have __path__ (not a valid package).
    """
    parts = migrations_package.rsplit(".", 1)
    if len(parts) == 1:
        module = importlib.import_module(migrations_package)
    else:
        module = importlib.import_module(parts[0])
        module = getattr(module, parts[1])
    
    if not hasattr(module, "__path__"):
        raise AttributeError(
            f"{migrations_package} is not a valid package (no __path__)"
        )
    
    return str(module.__path__[0])

