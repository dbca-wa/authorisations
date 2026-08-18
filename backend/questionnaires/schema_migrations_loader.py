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
    
    if from_idx <= to_idx:
        # Forward path
        return available[from_idx : to_idx + 1]
    else:
        # Backward path (reversed)
        return available[to_idx : from_idx + 1][::-1]
