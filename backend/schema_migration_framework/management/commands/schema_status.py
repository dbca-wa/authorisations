"""Generic management command to show schema migration status for any configured target."""

import importlib
from argparse import ArgumentParser
from collections import Counter
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from schema_migration_framework import (
    get_schema_version_from_document,
    get_target,
    get_target_model,
    list_migrations,
    load_targets,
)


class Command(BaseCommand):
    """Display schema migration status for a configured target."""

    help = "Show current schema version and record distribution for a target"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments."""
        parser.add_argument(
            "--target",
            type=str,
            required=True,
            help="Target key from SCHEMA_MIGRATION_TARGETS (e.g., 'questionnaires')",
        )

    def handle(self, target: str, **options: Any) -> None:
        """Display schema status for target.

        Shows current code version, database distribution by schema_version,
        available migrations, and warnings for error states (mixed versions).

        Args:
            target: Target key from SCHEMA_MIGRATION_TARGETS.

        Raises:
            CommandError: If target not found or configuration invalid.
        """
        # Load and look up target (trust startup validation)
        try:
            targets = load_targets()
        except Exception as e:
            raise CommandError(
                f"Failed to load migration targets configuration: {str(e)}"
            )

        target_config = get_target(target, targets)
        if not target_config:
            raise CommandError(
                f"Target '{target}' not found in SCHEMA_MIGRATION_TARGETS. "
                f"Available targets: {', '.join([t['key'] for t in targets])}"
            )

        # Get model and schema version constant
        try:
            Model = get_target_model(target_config)
        except Exception as e:
            raise CommandError(f"Cannot load model for target '{target}': {str(e)}")

        try:
            schema_module_path, schema_const_name = (
                target_config["schema_provider"].rsplit(".", 1)
            )
            schema_module = importlib.import_module(schema_module_path)
            code_version = getattr(schema_module, schema_const_name)
        except Exception as e:
            raise CommandError(
                f"Cannot load schema version constant for target '{target}': {str(e)}"
            )

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Schema Migration Status")
        self.stdout.write("=" * 70 + "\n")

        # Current code version
        self.stdout.write(f"Code schema version: {code_version}")

        # Record distribution
        try:
            distribution = self._get_distribution(Model, target_config)
        except Exception as e:
            raise CommandError(f"Failed to get record distribution: {str(e)}")

        # Database version (majority or error)
        if len(distribution) > 1:
            db_version = "MIXED/ERROR"
        elif distribution:
            db_version = next(iter(distribution.keys()))
        else:
            db_version = "EMPTY"

        self.stdout.write(f"Database schema version: {db_version}\n")

        # Record distribution
        self.stdout.write("Record distribution:")
        if not distribution:
            self.stdout.write("  (no records in database)")
        else:
            for version, count in sorted(distribution.items()):
                marker = " ✓" if version == code_version else ""
                self.stdout.write(f"  {version}: {count}{marker}")

        # Warnings
        if len(distribution) > 1:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  MIXED STATE: Records at {len(distribution)} different versions!"
                )
            )

        # Available migrations
        self.stdout.write("\nAvailable migrations:")
        try:
            migrations = list_migrations(
                target_config["migrations_package"]
            )
        except Exception as e:
            self.stdout.write(f"  (error loading migrations: {str(e)})")
            migrations = []

        if not migrations:
            self.stdout.write("  (no migrations defined)")
        else:
            for migration in migrations:
                self.stdout.write(f"  {migration}")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def _get_distribution(self, Model: type, target_config: dict) -> dict:
        """Get distribution of records by schema_version.

        Returns:
            Dictionary mapping schema_version to record count.
            Returns empty dict if no records in database.
        """
        records = Model.objects.all()

        if not records.exists():
            return {}

        # Extract schema_version from each document JSON field using version_path
        versions = []
        json_field = target_config["json_field"]
        version_path = target_config["version_path"]

        for record in records:
            doc = getattr(record, json_field)
            version = get_schema_version_from_document(doc, version_path)
            versions.append(version)

        return dict(Counter(versions))
