"""Type definitions and data structures for schema migration framework.

Provides TypedDict and other type hints for configuration and targets.
"""

from typing import TypedDict


class MigrationTarget(TypedDict):
    """Configuration for a single schema migration target.

    A target represents a JSONField in a Django model that contains versioned
    JSON documents. The framework uses this configuration to locate migrations,
    load version providers, and validate transforms.

    Example:
        {
            "key": "questionnaires",
            "model": "questionnaires.Questionnaire",
            "json_field": "document",
            "schema_provider": "questionnaires.schema.SCHEMA_VERSION",
            "migrations_package": "questionnaires.schema_migrations",
            "version_path": "schema_version",
        }
    """

    key: str
    """Unique identifier for this target. Used by commands to select which target to operate on.
    
    Example: "questionnaires", "applications"
    Must be URL-safe and unique across all registered targets.
    """

    model: str
    """Django model reference in 'app_label.ModelName' format.
    
    Example: "questionnaires.Questionnaire"
    Used to locate the model class and fetch records from database.
    """

    json_field: str
    """Name of the JSONField column containing versioned documents.
    
    Example: "document"
    On the model, this field must be a Django JSONField containing a dict with
    the document data and (in Phase 7-11) a schema_version key.
    """

    schema_provider: str
    """Dotted Python import path to the SCHEMA_VERSION constant.
    
    Example: "questionnaires.schema.SCHEMA_VERSION"
    Points to the single-source-of-truth integer constant that defines the
    current schema version. Dynamically imported to get current version.
    """

    migrations_package: str
    """Dotted Python package path to the schema_migrations directory.
    
    Example: "questionnaires.schema_migrations"
    The framework scans this package for migration files (0001_*.py, 0002_*.py, etc).
    """

    version_path: str
    """JSON key path to the schema version field inside the document.
    
    Example: "schema_version"
    For Phase 7-11, this is always "schema_version" (in-document storage only).
    Future: may support nested paths like "metadata.schema_version".
    """
