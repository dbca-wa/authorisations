"""Django AppConfig for schema migration framework.

Provides startup validation to catch configuration errors early.
"""

from django.apps import AppConfig

from .registry import load_targets


class SchemaMigrationFrameworkConfig(AppConfig):
    """App configuration for schema_migration_framework.
    
    Validates target configuration at Django startup.
    """

    name = "schema_migration_framework"
    verbose_name = "Schema Migration Framework"

    def ready(self) -> None:
        """Validate registry configuration at Django startup.

        Called when Django initialises this app. Raises RegistryError if
        SCHEMA_MIGRATION_TARGETS is missing or misconfigured, preventing
        the application from starting with invalid configuration.

        Raises:
            RegistryError: If configuration is invalid.
        """
        # Attempt to load targets. If configuration is invalid, this raises RegistryError
        # and prevents Django from fully starting.
        load_targets()
