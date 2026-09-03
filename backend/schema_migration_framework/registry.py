"""Registry for schema migration targets via Django settings.

Loads and validates `SCHEMA_MIGRATION_TARGETS` from Django settings,
enabling the framework to operate on multiple JSONField targets
(questionnaires, applications, etc.) without code changes.
"""

from typing import Optional

from django.conf import settings

from .types import MigrationTarget


class RegistryError(Exception):
    """Raised when registry configuration is invalid."""

    pass


def load_targets() -> list[MigrationTarget]:
    """Load migration targets from Django settings.

    Reads `SCHEMA_MIGRATION_TARGETS` from django.conf.settings and returns
    a list of validated target configurations.

    Returns:
        List of MigrationTarget dicts.

    Raises:
        RegistryError: If setting is missing, malformed, or contains invalid targets.

    Example:
        # In Django settings:
        SCHEMA_MIGRATION_TARGETS = [
            {
                "key": "questionnaires",
                "model": "questionnaires.Questionnaire",
                "json_field": "document",
                "schema_provider": "questionnaires.schema.SCHEMA_VERSION",
                "migrations_package": "questionnaires.schema_migrations",
                "version_path": "schema_version",
            }
        ]

        # In code:
        targets = load_targets()
        # → [MigrationTarget({...})]
    """
    if not hasattr(settings, "SCHEMA_MIGRATION_TARGETS"):
        raise RegistryError(
            "SCHEMA_MIGRATION_TARGETS setting not found in Django settings.\n"
            "Define SCHEMA_MIGRATION_TARGETS as a list of target configurations."
        )

    targets = settings.SCHEMA_MIGRATION_TARGETS

    if not isinstance(targets, list):
        raise RegistryError(
            f"SCHEMA_MIGRATION_TARGETS must be a list, got {type(targets).__name__}"
        )

    if not targets:
        raise RegistryError(
            "SCHEMA_MIGRATION_TARGETS is empty. Define at least one migration target."
        )

    # Validate each target
    for idx, target in enumerate(targets):
        _validate_target(target, idx)

    # Validate no duplicate keys
    validate_no_duplicate_keys(targets)

    return targets


def _validate_target(target: dict, index: int) -> None:
    """Validate a single target configuration.

    Args:
        target: Target dict to validate.
        index: Position in targets list (for error messages).

    Raises:
        RegistryError: If target is invalid.
    """
    if not isinstance(target, dict):
        raise RegistryError(
            f"Target {index}: Expected dict, got {type(target).__name__}"
        )

    # Check required fields
    required_fields = [
        "key",
        "model",
        "json_field",
        "schema_provider",
        "migrations_package",
        "version_path",
    ]

    for field in required_fields:
        if field not in target:
            raise RegistryError(
                f"Target {index} ({target.get('key', 'unknown')}): "
                f"Missing required field '{field}'"
            )

    # Validate field types
    if not isinstance(target["key"], str):
        raise RegistryError(
            f"Target {index}: 'key' must be string, got {type(target['key']).__name__}"
        )

    if not isinstance(target["model"], str):
        raise RegistryError(
            f"Target {index}: 'model' must be string, got {type(target['model']).__name__}"
        )

    if not isinstance(target["json_field"], str):
        raise RegistryError(
            f"Target {index}: 'json_field' must be string, got {type(target['json_field']).__name__}"
        )

    if not isinstance(target["schema_provider"], str):
        raise RegistryError(
            f"Target {index}: 'schema_provider' must be string, got {type(target['schema_provider']).__name__}"
        )

    if not isinstance(target["migrations_package"], str):
        raise RegistryError(
            f"Target {index}: 'migrations_package' must be string, got {type(target['migrations_package']).__name__}"
        )

    if not isinstance(target["version_path"], str):
        raise RegistryError(
            f"Target {index}: 'version_path' must be string, got {type(target['version_path']).__name__}"
        )

    # Validate model format (app_label.ModelName)
    if "." not in target["model"]:
        raise RegistryError(
            f"Target {index} ({target['key']}): 'model' must be in format 'app_label.ModelName', "
            f"got '{target['model']}'"
        )

    # Validate schema_provider format (dotted path)
    if "." not in target["schema_provider"]:
        raise RegistryError(
            f"Target {index} ({target['key']}): 'schema_provider' must be dotted import path "
            f"(e.g., 'app.module.CONSTANT'), got '{target['schema_provider']}'"
        )

    # Validate migrations_package format (dotted path)
    if "." not in target["migrations_package"]:
        raise RegistryError(
            f"Target {index} ({target['key']}): 'migrations_package' must be dotted import path "
            f"(e.g., 'app.schema_migrations'), got '{target['migrations_package']}'"
        )


def validate_no_duplicate_keys(targets: list[MigrationTarget]) -> None:
    """Validate that all target keys are unique.

    Args:
        targets: List of targets to check.

    Raises:
        RegistryError: If duplicate keys found.
    """
    keys = [target["key"] for target in targets]
    seen = set()

    for key in keys:
        if key in seen:
            raise RegistryError(
                f"Duplicate target key '{key}'. Target keys must be unique."
            )
        seen.add(key)


def get_target(key: str, targets: list[MigrationTarget]) -> Optional[MigrationTarget]:
    """Find a target by key.

    Args:
        key: Target key to find.
        targets: List of targets to search.

    Returns:
        Target dict if found, None otherwise.
    """
    for target in targets:
        if target["key"] == key:
            return target
    return None


def list_target_keys(targets: list[MigrationTarget]) -> list[str]:
    """Get all target keys in order.

    Args:
        targets: List of targets.

    Returns:
        List of target keys.
    """
    return [target["key"] for target in targets]
