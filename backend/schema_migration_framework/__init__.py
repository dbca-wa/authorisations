"""Schema Migration Framework - Generic, reusable JSON schema migration orchestration.

A Django-agnostic migration framework for managing versioned JSON documents stored
in JSONField columns. Provides migration loading, path resolution, transform validation,
and transaction-safe execution.

Core dependencies: Django, jsonschema (no DRF, no framework-specific integrations).

Design:
- Migration files: Stored in app-specific schema_migrations/ packages, define
  previous_schema(), target_schema(), migrate_forward(), migrate_backward()
- Loader: Discovers and imports migration modules dynamically by number
- Path resolution: Finds transformation sequences (forward/backward)
- Validator: Validates transforms against frozen schema definitions
- Executor: Applies migrations in transaction-scoped, idempotent manner
- Registry: Configurable multi-target support via Django settings (Phase 8+)

Version storage (Phase 7-11): In-document only (document["schema_version"]).
Future: Will support dedicated DB field (decision not yet made).

NOT INCLUDED: schema_zero emergency tool (standalone command, not framework).
"""

from .loader import (
    get_migration,
    list_migrations,
    migration_number_to_version,
    version_to_migration_number,
)
from .pathing import find_path
from .registry import (
    RegistryError,
    get_target,
    list_target_keys,
    load_targets,
)
from .types import MigrationTarget
from .validator import validate_transform
from .executor import (
    get_target_model,
    get_schema_version_from_document,
    get_migrations_package_path,
)

__all__ = [
    "get_migration",
    "list_migrations",
    "migration_number_to_version",
    "version_to_migration_number",
    "find_path",
    "validate_transform",
    "load_targets",
    "get_target",
    "list_target_keys",
    "RegistryError",
    "MigrationTarget",
    "get_target_model",
    "get_schema_version_from_document",
    "get_migrations_package_path",
]
