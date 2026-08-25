"""Management command to migrate questionnaires to a new schema version.

Usage:
    python manage.py schema_migrate_questionnaire 0002            # Migrate to version in 0002_*.py
    python manage.py schema_migrate_questionnaire 0004            # Auto-sequences: 0002, 0003, 0004
    python manage.py schema_migrate_questionnaire 0002 --dry-run  # Test without writing

Idempotency:
    Running the same migration target twice is safe. If already at target version,
    returns success (no-op). Each migration in the sequence runs in isolation.

Transaction safety:
    Each migration is applied in a separate database transaction. If migration N
    fails, records remain at the version produced by migration N-1. Retry with
    the same target to continue from where it failed.

Sequential execution:
    If database is at version produced by 0001 and you request 0004, the command
    automatically applies 0002, 0003, and 0004 in order.
"""

from copy import deepcopy

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from questionnaires.models import Questionnaire
from questionnaires.schema_migration_utils import (
    get_db_schema_version,
    validate_transform,
)
from questionnaires.schema_migrations_loader import (
    find_migration_by_output_version,
    find_path,
    get_migration,
    migration_number_to_version,
)


class Command(BaseCommand):
    """Migrate all questionnaire records forward to a target schema version."""

    help = "Migrate questionnaires to a new schema version"

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            "migration_number",
            type=str,
            help="Migration number to migrate to (e.g., 0002)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Test migration without writing to database",
        )

    def handle(self, migration_number, dry_run=False, **options):
        """Execute schema migration to target version.

        Automatically finds and applies all intermediate migrations in sequence.
        Each migration runs in isolation with its own transaction.

        Args:
            migration_number: Target migration number (e.g., "0004")
            dry_run: If True, test without writing to database

        Raises:
            CommandError: If migration cannot proceed (version mismatch, validation error, etc.)
        """
        # Validate the requested migration exists
        try:
            get_migration(migration_number)
        except FileNotFoundError:
            raise CommandError(f"Migration {migration_number} not found")

        target_version = migration_number_to_version(migration_number)
        current_db_version = get_db_schema_version()

        # IDEMPOTENCY CHECK: Already at target version?
        if current_db_version == target_version:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No migration needed."
                )
            )
            return

        # Get all records
        questionnaires = list(Questionnaire.objects.all())
        record_count = len(questionnaires)

        # EMPTY DATABASE: No-op (nothing to migrate)
        if record_count == 0:
            self.stdout.write(self.style.WARNING("No questionnaires found to migrate."))
            return

        # Find which migration number produces current version
        try:
            current_migration_number = find_migration_by_output_version(current_db_version)
        except ValueError as e:
            raise CommandError(
                f"Cannot determine migration path:\n{str(e)}\n"
                f"Run 'python manage.py schema_status_questionnaire' to diagnose."
            )

        # Find path from current to target
        try:
            path = find_path(current_migration_number, migration_number)
        except ValueError as e:
            raise CommandError(f"Cannot find migration path: {str(e)}")

        # Remove the first migration (already applied, current state)
        # EXCEPT if we're starting from baseline ("0000"), in which case we need all migrations
        if current_migration_number == "0000":
            migrations_to_apply = path
        else:
            migrations_to_apply = path[1:]

        if not migrations_to_apply:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No migration needed."
                )
            )
            return

        self.stdout.write(
            f"Found {record_count} questionnaire(s) at version {current_db_version}"
        )
        self.stdout.write(
            f"Migration path: {' → '.join(path)}\n"
        )

        # Apply each migration in sequence
        current_version = current_db_version
        for migration_num in migrations_to_apply:
            migration = get_migration(migration_num)
            next_version = migration_number_to_version(migration_num)

            self.stdout.write(f"Applying migration {migration_num} ({current_version} → {next_version})...")

            if dry_run:
                self.stdout.write("  [DRY RUN] Testing transforms without writing...\n")
                self._test_transforms(questionnaires, migration, current_version, next_version)
                current_version = next_version
                continue

            # Apply in transaction (each migration independently)
            try:
                with transaction.atomic():
                    self._test_transforms(questionnaires, migration, current_version, next_version)
                    self._apply_transforms(questionnaires, migration)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Migration {migration_num} complete: {record_count} record(s) updated to {next_version}\n"
                    )
                )
                current_version = next_version
            except Exception as e:
                raise CommandError(
                    f"Migration {migration_num} failed:\n{str(e)}\n"
                    f"Records remain at version {current_version}. "
                    f"Fix the issue and retry with: python manage.py schema_migrate_questionnaire {migration_number}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Successfully migrated to version {target_version}"
            )
        )

    def _test_transforms(self, questionnaires, migration, from_version, to_version):
        """Validate all transforms before applying.

        Args:
            questionnaires: List of Questionnaire objects
            migration: Migration module with transform functions
            from_version: Current schema version before transform
            to_version: Target schema version after transform

        Raises:
            CommandError: If validation fails for any record
        """
        from_schema = migration.previous_schema()
        to_schema = migration.target_schema()

        success_count = 0
        failed_records = []

        for questionnaire in questionnaires:
            doc = questionnaire.document

            # Test the transform
            try:
                transformed = deepcopy(doc)
                transformed = migration.migrate_forward(transformed)

                # Validate transformed document
                is_valid, errors = validate_transform(
                    transformed,
                    from_version,
                    to_version,
                    from_schema,
                    to_schema,
                )

                if not is_valid:
                    failed_records.append(
                        (questionnaire.id, f"Validation failed: {', '.join(errors)}")
                    )
                else:
                    success_count += 1
            except Exception as e:
                failed_records.append((questionnaire.id, str(e)))

        # Report results
        self.stdout.write(f"Tested {success_count}/{len(questionnaires)}")

        if failed_records:
            errors = "\n".join(
                [f"  - Record {rec_id}: {err}" for rec_id, err in failed_records]
            )
            raise CommandError(
                f"Validation failed for {len(failed_records)} record(s):\n{errors}"
            )

    def _apply_transforms(self, questionnaires, migration):
        """Apply transformation to all records (called within transaction).

        Args:
            questionnaires: List of Questionnaire objects
            migration: Migration module with migrate_forward function
        """
        for questionnaire in questionnaires:
            questionnaire.document = migration.migrate_forward(questionnaire.document)
            questionnaire.save(update_fields=["document"])
