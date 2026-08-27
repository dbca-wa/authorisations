"""Generic management command to rollback records to a previous schema version for any target."""

from copy import deepcopy
from typing import Any
from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from schema_migration_framework import (
    find_path,
    get_migration,
    get_migrations_package_path,
    get_schema_version_from_document,
    get_target,
    get_target_model,
    list_migrations,
    load_targets,
    migration_number_to_version,
    validate_transform,
)
from schema_migration_framework.loader import find_migration_by_output_version


class Command(BaseCommand):
    """Rollback all records for a target to a previous schema version."""

    help = "Rollback target records to a previous schema version"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments."""
        parser.add_argument(
            "--target",
            type=str,
            required=True,
            help="Target key from SCHEMA_MIGRATION_TARGETS (e.g., 'questionnaires')",
        )
        parser.add_argument(
            "migration_number",
            type=str,
            help="Migration number to rollback to (e.g., 0001)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Test rollback without writing to database",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed progress per record",
        )

    def handle(self, target: str, migration_number: str, dry_run: bool = False, verbose: bool = False, **options: Any) -> None:
        """Execute schema rollback to previous version.

        Automatically finds and applies all intermediate migrations backwards in sequence.
        Each migration runs in isolation with its own transaction.

        Args:
            target: Target key from SCHEMA_MIGRATION_TARGETS.
            migration_number: Target migration number to rollback to (e.g., "0001").
            dry_run: If True, test without writing to database.
            verbose: If True, show per-record progress.

        Raises:
            CommandError: If rollback cannot proceed.
        """
        # Prevent rollback to version 0 (no migration file exists before baseline)
        target_version = migration_number_to_version(migration_number)
        if target_version == 0:
            raise CommandError(
                "Cannot rollback to version 0 (baseline). Version 0 exists only before "
                "any migrations are applied. To reset data, use schema_zero tool instead."
            )

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
                f"Target '{target}' not found in SCHEMA_MIGRATION_TARGETS"
            )

        # Convert dotted migrations_package to filesystem path
        try:
            migrations_package_path = get_migrations_package_path(
                target_config["migrations_package"]
            )
        except Exception as e:
            raise CommandError(
                f"Cannot load migrations package for target '{target}': {str(e)}"
            )

        # Validate migration exists
        try:
            get_migration(migration_number, migrations_package_path)
        except FileNotFoundError:
            raise CommandError(f"Migration {migration_number} not found")

        # Get model
        try:
            Model = get_target_model(target_config)
        except Exception as e:
            raise CommandError(f"Cannot load model for target '{target}': {str(e)}")

        json_field = target_config["json_field"]
        version_path = target_config["version_path"]

        # Get current DB version
        records = list(Model.objects.all())
        record_count = len(records)

        if not records:
            self.stdout.write(
                self.style.WARNING(f"No {target} records found to rollback.")
            )
            return

        current_db_version = self._get_db_version(records, json_field, version_path)

        # IDEMPOTENCY CHECK
        if current_db_version == target_version:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No rollback needed."
                )
            )
            return

        # Validate rollback direction (must go backwards)
        if current_db_version < target_version:
            raise CommandError(
                f"Cannot rollback from version {current_db_version} to {target_version}. "
                f"Target version is newer. Use schema_migrate to go forward instead."
            )

        # Load available migrations
        available_migrations = list_migrations(migrations_package_path)
        if not available_migrations:
            raise CommandError("No migrations available.")

        # Find current migration number
        if current_db_version == 0:
            raise CommandError(
                "Database is at version 0 (baseline). Cannot rollback further. "
                "No migration file exists before baseline."
            )

        try:
            current_migration_number = find_migration_by_output_version(
                current_db_version, migrations_package_path
            )
        except ValueError as e:
            raise CommandError(
                f"Cannot determine current migration:\n{str(e)}\n"
                f"Run 'python manage.py schema_status --target {target}' to diagnose."
            )

        # Find path from current backwards to target
        try:
            forward_path = find_path(
                current_migration_number, migration_number, available_migrations
            )
        except ValueError as e:
            raise CommandError(f"Cannot find rollback path: {str(e)}")

        # Reverse the path for backward application
        backward_path = list(reversed(forward_path))
        
        # Remove the first migration (already at current state)
        migrations_to_rollback = backward_path[1:]

        if not migrations_to_rollback:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No rollback needed."
                )
            )
            return

        self.stdout.write(
            f"Found {record_count} {target} record(s) at version {current_db_version}"
        )
        self.stdout.write(f"Rollback path: {' ← '.join(backward_path)}\n")

        # Apply each rollback migration in sequence
        current_version = current_db_version
        for migration_num in migrations_to_rollback:
            migration = get_migration(migration_num, migrations_package_path)
            next_version = migration_number_to_version(migration_num)

            self.stdout.write(
                f"Rolling back migration {migration_num} ({current_version} ← {next_version})..."
            )

            if dry_run:
                self.stdout.write("  [DRY RUN] Testing rollback transforms without writing...\n")
                self._test_backward_transforms(
                    records, migration, current_version, next_version, verbose
                )
                current_version = next_version
                continue

            # Apply in transaction (each migration independently)
            try:
                with transaction.atomic():
                    self._test_backward_transforms(
                        records, migration, current_version, next_version, verbose
                    )
                    self._apply_backward_transforms(records, migration, json_field)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Rollback {migration_num} complete: {record_count} record(s) rolled back to {next_version}\n"
                    )
                )
                current_version = next_version
            except Exception as e:
                raise CommandError(
                    f"Rollback {migration_num} failed:\n{str(e)}\n"
                    f"Records remain at version {current_version}. "
                    f"Fix the issue and retry with: python manage.py schema_rollback --target {target} {migration_number}"
                )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully rolled back to version {target_version}")
        )

    def _test_backward_transforms(
        self, records: list[Any], migration: Any, from_version: int | str, to_version: int | str, verbose: bool
    ) -> None:
        """Validate all backward transforms before applying.

        Args:
            records: List of model records.
            migration: Migration module with transform functions.
            from_version: Current schema version before rollback.
            to_version: Target schema version after rollback.
            verbose: If True, show per-record progress.

        Raises:
            CommandError: If validation fails for any record.
        """
        previous_schema = migration.previous_schema()
        success_count = 0
        failed_records = []

        for record in records:
            doc = record.document if hasattr(record, "document") else record.__dict__.get("document")

            try:
                transformed = deepcopy(doc)
                transformed = migration.migrate_backward(transformed)

                # Validate backward-transformed document against previous schema
                is_valid, errors = validate_transform(
                    transformed,
                    to_version,
                    from_version,
                    previous_schema,
                    migration.target_schema(),
                )

                if not is_valid:
                    failed_records.append(
                        (record.id, f"Validation failed: {', '.join(errors)}")
                    )
                else:
                    success_count += 1
                    if verbose:
                        self.stdout.write(f"    ✓ Record {record.id}")
            except Exception as e:
                failed_records.append((record.id, str(e)))
                if verbose:
                    self.stdout.write(self.style.WARNING(f"    ✗ Record {record.id}: {str(e)}"))

        self.stdout.write(f"Tested {success_count}/{len(records)}")

        if failed_records:
            errors = "\n".join(
                [f"  - Record {rec_id}: {err}" for rec_id, err in failed_records]
            )
            raise CommandError(
                f"Validation failed for {len(failed_records)} record(s):\n{errors}"
            )

    def _apply_backward_transforms(self, records: list[Any], migration: Any, json_field: str) -> None:
        """Apply backward transformation to all records (called within transaction).

        Args:
            records: List of model records.
            migration: Migration module with migrate_backward function.
            json_field: Name of JSON field containing document.
        """
        for record in records:
            doc = getattr(record, json_field)
            setattr(record, json_field, migration.migrate_backward(doc))
            record.save(update_fields=[json_field])

    def _get_db_version(self, records: list[Any], json_field: str, version_path: str) -> int:
        """Get current schema version from records using version_path.

        Args:
            records: List of model records.
            json_field: Name of JSON field.
            version_path: Path to version in document (dot notation).

        Returns:
            Current schema version if all records match, raises error otherwise.

        Raises:
            RuntimeError: If records have mixed versions.
        """
        if not records:
            return 0

        versions = set()
        for record in records:
            doc = getattr(record, json_field)
            version = get_schema_version_from_document(doc, version_path)
            versions.add(version)

        if len(versions) > 1:
            raise RuntimeError(
                f"Database contains records at multiple schema versions: {versions}. "
                f"This indicates a failed or partial migration."
            )

        return next(iter(versions)) if versions else 0
