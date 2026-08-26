"""Migration path resolution between schema versions.

Given a source and target migration number, finds the transformation path
(sequence of migrations) to go from source to target.
"""


def find_path(from_number: str, to_number: str, available_migrations: list[str]) -> list[str]:
    """Find transformation path between two migration numbers.
    
    Args:
        from_number: Starting migration number (e.g., "0001").
        to_number: Target migration number (e.g., "0003").
        available_migrations: Sorted list of all available migration numbers
    
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
