"""Migration path resolution between schema versions.

Finds transformation path (sequence of migrations) to go from current version
to target migration. Handles version type conversion (int or str) and filters
the path to return only migrations that need applying.
"""

from schema_migration_framework.loader import migration_number_to_version


def find_path(
    from_number: str, to_number: str, available_migrations: list[str]
) -> list[str]:
    """Find transformation path between two migration numbers (pure path finding).

    Args:
        from_number: Starting migration number (e.g., "0001").
        to_number: Target migration number (e.g., "0003").
        available_migrations: Sorted list of all available migration numbers.

    Returns:
        Sorted list of migration numbers representing the path.
        For forward: ascending order (0001, 0002, 0003).
        For backward: descending order (0003, 0002, 0001).

    Raises:
        ValueError: If from_number or to_number not found in available migrations.
    """
    if from_number not in available_migrations:
        raise ValueError(
            f"Migration {from_number} not found in available migrations. "
            f"Available: {available_migrations}"
        )

    if to_number not in available_migrations:
        raise ValueError(
            f"Migration {to_number} not found in available migrations. "
            f"Available: {available_migrations}"
        )

    from_idx = available_migrations.index(from_number)
    to_idx = available_migrations.index(to_number)

    if from_idx < to_idx:
        # Forward path: ascending sequence
        return available_migrations[from_idx : to_idx + 1]
    elif from_idx > to_idx:
        # Backward path: descending sequence
        return available_migrations[to_idx : from_idx + 1][::-1]
    else:
        # Same position (from == to)
        return [from_number]


def find_migrations_to_apply(
    from_version: int | str,
    to_migration_number: str,
    available_migrations: list[str],
) -> list[str]:
    """Find migrations to apply from current version to target.

    Handles version-to-migration lookup and filters path to return only
    migrations that need to be applied (skips any already applied).

    Args:
        from_version: Current schema version (int like 1, 2 or str like "2025.07-1").
        to_migration_number: Target migration number (e.g., "0003").
        available_migrations: Sorted list of all available migration numbers.
        migrations_package_path: Filesystem path to migrations package.

    Returns:
        Filtered list of migration numbers ready to apply.
        - For v0 or calendar versions: includes all migrations up to target
        - For v1+: skips first (represents current state), includes rest

    Raises:
        ValueError: If from_version cannot be resolved or to_migration_number not found.
    """
    # Handle the non-integer immediately
    if not isinstance(from_version, int) and "0000" in available_migrations:
        from_version = 0

    # Find the first matching migration number for the current version
    try:
        start_migration = next(
            m
            for m in available_migrations
            if migration_number_to_version(m) == from_version
        )
    except StopIteration:
        # `from_version` is not integer
        additional_text = (
            "Create a '0000' migration to bridge from non-integer versions; 0000_initial.py is a common pattern. \n"
            if not isinstance(from_version, int)
            else ""
        )

        raise ValueError(
            f"Cannot find migration for current version {from_version}. \n"
            f"{additional_text}"
            f"Available migrations: {', '.join(available_migrations)}"
        )

    # Find path from current migration to target
    return find_path(start_migration, to_migration_number, available_migrations)
