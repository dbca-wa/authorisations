"""Load and manage schema migration files for questionnaires module.

Provides utilities to discover, load, and resolve transformation paths between
schema versions. All migration files must be stored in the schema_migrations/
directory and contain a SCHEMA_VERSION constant.
"""

import importlib.util
import sys
from pathlib import Path


def get_migration(migration_number: str):
    """Load and return a migration module by number.
    
    Args:
        migration_number: Migration number as string (e.g., "0001", "0002").
                         Used to locate schema_migrations/XXXX_*.py file.
    
    Returns:
        Loaded migration module with SCHEMA_VERSION, previous_schema(),
        migrate_forward(), and migrate_backward() defined.
    
    Raises:
        FileNotFoundError: If migration file not found.
        AttributeError: If migration missing required SCHEMA_VERSION constant.
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
    
    # Verify required components exist
    if not hasattr(module, "SCHEMA_VERSION"):
        raise AttributeError(
            f"Migration {migration_number} missing SCHEMA_VERSION constant"
        )
    
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
    
    Handles the special case of "0000" which represents the pre-migration
    baseline version (e.g., "2025.07-1" before migration 0001 is applied).
    
    Args:
        from_number: Starting migration number (e.g., "0001") or "0000" for baseline.
        to_number: Target migration number (e.g., "0003") or "0000" for baseline.
    
    Returns:
        Sorted list of migration numbers representing the path.
        For forward: ascending order (0001, 0002, 0003).
        For backward: descending order (0003, 0002, 0001).
    
    Raises:
        ValueError: If from_number or to_number not found in available migrations.
    """
    available = list_migrations()
    
    # Handle special "0000" marker for pre-migration baseline
    if from_number == "0000":
        from_idx = -1  # Before all migrations
    elif from_number not in available:
        raise ValueError(f"Migration {from_number} not found in available migrations")
    else:
        from_idx = available.index(from_number)
    
    if to_number == "0000":
        to_idx = -1  # Before all migrations
    elif to_number not in available:
        raise ValueError(f"Migration {to_number} not found in available migrations")
    else:
        to_idx = available.index(to_number)
    
    if from_idx < to_idx:
        # Forward path
        start_idx = 0 if from_idx == -1 else from_idx
        return available[start_idx : to_idx + 1]
    elif from_idx > to_idx:
        # Backward path
        end_idx = -1 if to_idx == -1 else to_idx
        if end_idx == -1:
            # Backward from some migration to baseline: return all from that migration down
            return available[from_idx : :-1]
        else:
            return available[to_idx : from_idx + 1][::-1]
    else:
        # Same position
        return [from_number] if from_number != "0000" else []


def find_migration_by_output_version(target_version: str) -> str:
    """Find which migration number produces a given schema version.
    
    Given a schema version string (e.g., "1"), returns the migration number
    that produces it as output (e.g., "0001"). Handles the special case of the
    pre-migration baseline version (e.g., "2025.07-1") which is not produced
    by any migration but is the input to migration 0001.
    
    Args:
        target_version: Schema version string to find (e.g., "1", "2", "2025.07-1").
    
    Returns:
        Migration number that produces this version (e.g., "0001"), or special
        marker "0000" if this is the pre-migration baseline version.
    
    Raises:
        ValueError: If no migration produces the given version and it's not a known baseline.
    """
    available = list_migrations()
    
    # Check if this version is produced by any migration
    for migration_number in available:
        migration = get_migration(migration_number)
        if migration.SCHEMA_VERSION == target_version:
            return migration_number
    
    # Special case: Check if this is the input version of the first migration (baseline)
    if available:
        first_migration = get_migration(available[0])
        first_schema = first_migration.previous_schema()
        baseline_version = first_schema.get("properties", {}).get("schema_version", {}).get("default")
        
        if baseline_version == target_version:
            # This is the pre-migration baseline version
            return "0000"
    
    raise ValueError(
        f"No migration found that produces schema version '{target_version}'. "
        f"Available migrations produce versions: "
        f"{[get_migration(m).SCHEMA_VERSION for m in available]}"
    )


def get_migration_previous_version(migration_number: str) -> str:
    """Get the schema version of the migration before the target migration.
    
    Used by management commands to verify preconditions: the database should be
    at the previous version before migrating to the target version.
    
    Args:
        migration_number: Target migration number (e.g., "0002").
    
    Returns:
        SCHEMA_VERSION from the previous migration (e.g., "1" for migration 0002).
    
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
