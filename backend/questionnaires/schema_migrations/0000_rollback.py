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
import importlib.util
import sys
from pathlib import Path


def _load_0001_initial_module():
    """Dynamically load the 0001_initial migration module.
    
    Module names starting with digits cannot be imported normally, so we use
    importlib.util to load them by file path. This is the same approach the
    framework uses internally.
    """
    migration_dir = Path(__file__).parent
    migration_file = migration_dir / "0001_initial.py"
    
    module_name = "schema_migrations.0001"
    spec = importlib.util.spec_from_file_location(module_name, migration_file)
    
    if spec is None or spec.loader is None:
        raise ImportError("Failed to load 0001_initial migration module")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    
    return module


# Load 0001_initial at module level for use in functions below
_migration_0001 = _load_0001_initial_module()

# Target-specific calendar version for questionnaires
_CALENDAR_VERSION = "2025.07-1"


def target_schema():
    """Return the schema structure for version 0 (integer baseline).
    
    This is the state AFTER rollback completes. Identical to 0001's previous_schema
    (the v0 integer version state).
    """
    return _migration_0001.previous_schema()


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
    if doc.get("schema_version") != _CALENDAR_VERSION:
        raise TypeError(
            f"Expected schema_version '{_CALENDAR_VERSION}', got {doc.get('schema_version')}"
        )
    
    doc = deepcopy(doc)
    doc["schema_version"] = 0
    return doc


