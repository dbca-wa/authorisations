"""Migration file discovery and dynamic importing.

Discovers migration files by number in a target package and dynamically imports
them as Python modules. Migration files follow naming convention: XXXX_description.py
(e.g., 0001_initial.py, 0002_consolidate.py).

Migration modules must provide:
- previous_schema() -> dict: Hard-coded schema snapshot for previous version
- target_schema() -> dict: Hard-coded schema snapshot for target version
- migrate_forward(doc: dict) -> dict: Transform doc from previous → target
- migrate_backward(doc: dict) -> dict: Transform doc from target → previous
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def migration_number_to_version(migration_number: str) -> int:
    """Convert migration number string to schema version integer.
    
    Args:
        migration_number: Migration number as string (e.g., "0001", "0002").
    
    Returns:
        Schema version as integer (e.g., 1, 2).
    
    Raises:
        ValueError: If migration_number cannot be converted to integer.
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


def get_migration(migration_number: str, migrations_package_path: str) -> ModuleType:
    """Load and return a migration module by number.
    
    Args:
        migration_number: Migration number as string (e.g., "0001", "0002").
                         Used to locate XXXX_*.py file.
        migrations_package_path: Absolute filesystem path to migrations package
                                (e.g., "/path/to/backend/questionnaires/schema_migrations")
    
    Returns:
        Loaded migration module with previous_schema(), target_schema(),
        migrate_forward(), and migrate_backward() defined.
    
    Raises:
        FileNotFoundError: If migration file not found.
        ImportError: If migration fails to load.
        RuntimeError: If multiple migration files match the same number (ambiguous).
    """
    migrations_dir = Path(migrations_package_path)
    
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
    module_name = f"schema_migrations.{migration_number}"
    spec = importlib.util.spec_from_file_location(module_name, migration_file)
    
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load migration {migration_number}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    
    return module


def list_migrations(migrations_package_path: str) -> list[str]:
    """Return all available migration numbers in order.
    
    Args:
        migrations_package_path: Absolute filesystem path to migrations package
    
    Returns:
        Sorted list of migration numbers (e.g., ["0001", "0002", "0003"]).
        Returns empty list if no migrations found.
    """
    migrations_dir = Path(migrations_package_path)
    
    if not migrations_dir.exists():
        return []
    
    # Find all migration files matching pattern XXXX_*.py (but not __pycache__)
    migration_numbers = sorted(
        set(
            f.stem.split("_")[0]
            for f in migrations_dir.glob("????_*.py")
            if f.is_file() and not f.name.startswith(".")
        )
    )
    
    return migration_numbers


def find_migration_by_output_version(target_version: int, migrations_package_path: str) -> str:
    """Find which migration number produces a given schema version.

    Converts an ordinal schema version to its corresponding migration number
    (e.g., version 1 → "0001", version 2 → "0002") and validates that the
    migration exists in the available migrations.

    Args:
        target_version: Ordinal schema version as integer (e.g., 1, 2, 3).
        migrations_package_path: Absolute filesystem path to migrations package.

    Returns:
        Migration number as 4-digit zero-padded string (e.g., "0001", "0002").

    Raises:
        ValueError: If the migration for target_version does not exist in available migrations.
    """
    target_migration_number = version_to_migration_number(target_version)
    available = list_migrations(migrations_package_path)

    if target_migration_number not in available:
        raise ValueError(
            f"No migration found that produces version {target_version}. "
            f"Available migrations: {', '.join(available) if available else '(none)'}"
        )

    return target_migration_number
