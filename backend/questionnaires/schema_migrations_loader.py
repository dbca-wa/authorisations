"""Load and manage schema migration files for questionnaires module.

Provides utilities to discover, load, and resolve transformation paths between
schema versions. Schema versions are derived from migration file prefixes
(e.g., "0001" → version 1, "0002" → version 2).
"""

import importlib.util
import sys
from pathlib import Path


def migration_number_to_version(migration_number: str) -> int:
    """Convert migration number to schema version integer.
    
    Args:
        migration_number: Migration number as string (e.g., "0001", "0002").
    
    Returns:
        Schema version as integer (e.g., 1, 2).
    
    Raises:
        ValueError: If migration_number cannot be converted.
    """
    try:
        return int(migration_number)
    except ValueError:
        raise ValueError(
            f"Invalid migration number '{migration_number}'. "
            f"Must be numeric string (e.g., '0001', '0002')"
        )


def version_to_migration_number(version: int) -> str:
    """Convert schema version integer to migration number string.
    
    Args:
        version: Schema version as integer (e.g., 1, 2).
    
    Returns:
        Migration number as 4-digit zero-padded string (e.g., "0001", "0002").
    """
    return f"{version:04d}"


def get_migration(migration_number: str):
    """Load and return a migration module by number.
    
    Args:
        migration_number: Migration number as string (e.g., "0001", "0002").
                         Used to locate schema_migrations/XXXX_*.py file.
    
    Returns:
        Loaded migration module with previous_schema(), target_schema(),
        migrate_forward(), and migrate_backward() defined.
    
    Raises:
        FileNotFoundError: If migration file not found.
        ImportError: If migration fails to load.
    """
    migrations_dir = Path(__file__).parent / "schema_migrations"
    
    # Find migration file matching pattern 0001_*.py, 0002_*.py, etc.
    matching_files = list(migrations_dir.glob(f"{migration_number}_*.py"))
    
    if not matching_files:
        raise FileNotFoundError(
            f"Migration {migration_number} not found in {migrations_dir}"
        )
    
    # Check for duplicate migration files (ambiguous state)
    if len(matching_files) > 1:
        raise RuntimeError(
            f"Expected exactly 1 migration file for {migration_number}, "
            f"found {len(matching_files)}: {[f.name for f in matching_files]}. "
            f"Migration numbers must be unique."
        )
    
    migration_file = matching_files[0]
    
    # Dynamically import the migration module
    spec = importlib.util.spec_from_file_location(
        f"questionnaires.schema_migrations.{migration_number}",
        migration_file,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load migration {migration_number}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    
    return module


def list_migrations() -> list[str]:
    """Return all available migration numbers in order.
    
    Returns:
        Sorted list of migration numbers (e.g., ["0001", "0002", "0003"]).
        Returns empty list if no migrations found.
    """
    migrations_dir = Path(__file__).parent / "schema_migrations"
    
    if not migrations_dir.exists():
        return []
    
    # Find all migration files matching pattern XXXX_*.py (but not __pycache__)
    migration_files = sorted(
        f.stem.split("_")[0]
        for f in migrations_dir.glob("????_*.py")
        if f.is_file() and not f.name.startswith(".")
    )
    
    # Remove duplicates and sort
    return sorted(list(set(migration_files)))


def find_path(from_number: str, to_number: str) -> list[str]:
    """Find transformation path between two migration numbers.
    
    Args:
        from_number: Starting migration number (e.g., "0001").
        to_number: Target migration number (e.g., "0003").
    
    Returns:
        Sorted list of migration numbers representing the path.
        For forward: ascending order (0001, 0002, 0003).
        For backward: descending order (0003, 0002, 0001).
    
    Raises:
        ValueError: If from_number or to_number not found in available migrations.
    """
    available = list_migrations()
    
    if from_number not in available:
        raise ValueError(f"Migration {from_number} not found in available migrations")
    
    if to_number not in available:
        raise ValueError(f"Migration {to_number} not found in available migrations")
    
    from_idx = available.index(from_number)
    to_idx = available.index(to_number)
    
    if from_idx < to_idx:
        # Forward path
        return available[from_idx : to_idx + 1]
    elif from_idx > to_idx:
        # Backward path
        return available[to_idx : from_idx + 1][::-1]
    else:
        # Same position
        return [from_number]


def find_migration_by_output_version(target_version: int) -> str:
    """Find which migration number produces a given schema version.
    
    Given a schema version integer (e.g., 1, 2), returns the migration number
    that produces it as output (e.g., "0001").
    
    Schema versions are derived from migration file prefixes. Migration 0001
    produces version 1, migration 0002 produces version 2, etc.
    
    Args:
        target_version: Schema version integer to find (e.g., 1, 2).
    
    Returns:
        Migration number that produces this version (e.g., "0001").
    
    Raises:
        ValueError: If target_version is negative or no valid migration exists.
    """
    if target_version < 1:
        raise ValueError(
            f"Schema version must be positive (version 1 or higher), got {target_version}"
        )
    
    available = list_migrations()
    migration_number = version_to_migration_number(target_version)
    
    if migration_number not in available:
        raise ValueError(
            f"No migration produces schema version {target_version}. "
            f"Available migrations: {available}"
        )
    
    return migration_number


def get_migration_previous_version(migration_number: str) -> int:
    """Get the schema version of the migration before the target migration.
    
    Used by management commands to verify preconditions: the database should be
    at the previous version before migrating to the target version.
    
    Args:
        migration_number: Target migration number (e.g., "0002").
    
    Returns:
        SCHEMA_VERSION from the previous migration as integer (e.g., 1 for migration 0002).
    
    Raises:
        ValueError: If migration_number is 0001 (no previous migration) or not found.
    """
    available = list_migrations()
    
    if migration_number not in available:
        raise ValueError(f"Migration {migration_number} not found")
    
    idx = available.index(migration_number)
    
    if idx == 0:
        raise ValueError(
            f"Migration {migration_number} is the first migration (0001). "
            f"No previous version exists."
        )
    
    previous_number = available[idx - 1]
    previous_migration = get_migration(previous_number)
    
    return previous_migration.SCHEMA_VERSION
