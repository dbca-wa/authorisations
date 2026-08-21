"""Management command to rollback questionnaires to a previous schema version.

Usage:
    python manage.py schema_rollback_questionnaire 0001            # Rollback to version in 0001_*.py
    python manage.py schema_rollback_questionnaire 0001 --dry-run  # Test without writing

Idempotency:
    Running the same rollback target twice is safe. If already at target version,
    returns success (no-op). Each migration in the sequence runs in isolation.

Transaction safety:
    Each migration is applied in a separate database transaction. If migration N
    fails, records remain at the version produced by migration N+1. Retry with
    the same target to continue from where it failed.

Sequential execution (backward):
    If database is at version produced by 0004 and you request 0001, the command
    automatically applies 0004, 0003, and 0002 backward transforms in order.

Data rollback requires new code:
    To rollback data, the migration file with migrate_backward() must exist in
    the deployed code. This is why you rollback data BEFORE deploying old code.
"""

from copy import deepcopy
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from questionnaires.models import Questionnaire
from questionnaires.schema_migrations_loader import (
    get_migration,
    find_path,
    find_migration_by_output_version,
)
from questionnaires.schema_migration_utils import validate_transform, get_db_schema_version


class Command(BaseCommand):
    """Rollback all questionnaire records to a previous schema version."""

    help = "Rollback questionnaires to a previous schema version"

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            "migration_number",
            type=str,
            help="Target migration number to rollback to (e.g., 0001)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Test rollback without writing to database",
        )

    def handle(self, migration_number, dry_run=False, **options):
        """Execute schema rollback to target version.

        Automatically finds and applies all intermediate rollback migrations in sequence.
        Each migration runs in isolation with its own transaction.

        Args:
            migration_number: Target migration number to rollback to (e.g., "0001")
            dry_run: If True, test without writing to database

        Raises:
            CommandError: If rollback cannot proceed (version mismatch, validation error, etc.)
        """
        try:
            target_migration = get_migration(migration_number)
        except FileNotFoundError:
            raise CommandError(f"Migration {migration_number} not found")

        target_version = target_migration.SCHEMA_VERSION
        current_db_version = get_db_schema_version()

        # IDEMPOTENCY CHECK: Already at target version?
        if current_db_version == target_version:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No rollback needed."
                )
            )
            return

        # Get all records
        questionnaires = list(Questionnaire.objects.all())
        record_count = len(questionnaires)

        # EMPTY DATABASE: No-op (nothing to rollback)
        if record_count == 0:
            self.stdout.write(self.style.WARNING("No questionnaires found to rollback."))
            return

        # Find which migration number produces current version
        try:
            current_migration_number = find_migration_by_output_version(current_db_version)
        except ValueError as e:
            raise CommandError(
                f"Cannot determine rollback path:\n{str(e)}\n"
                f"Run 'python manage.py schema_status_questionnaire' to diagnose."
            )

        # Find path from current to target (backward path)
        try:
            path = find_path(current_migration_number, migration_number)
        except ValueError as e:
            raise CommandError(f"Cannot find rollback path: {str(e)}")

        # Remove the first migration (already applied, current state)
        migrations_to_rollback = path[1:]

        if not migrations_to_rollback:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Already at version {target_version}. No rollback needed."
                )
            )
            return

        self.stdout.write(
            f"Found {record_count} questionnaire(s) at version {current_db_version}"
        )
        self.stdout.write(
            f"Rollback path: {' → '.join(path)}\n"
        )

        # Apply each rollback migration in sequence
        current_version = current_db_version
        for migration_num in migrations_to_rollback:
            migration = get_migration(migration_num)
            # For rollback, the "previous" is the target (lower version)
            previous_version = migration.previous_schema().get("properties", {}).get("schema_version", {}).get("default")

            self.stdout.write(f"Rolling back migration {migration_num} ({current_version} → {previous_version})...")

            if dry_run:
                self.stdout.write("  [DRY RUN] Testing rollback transforms without writing...\n")
                self._test_rollback(questionnaires, migration, current_version, previous_version)
                current_version = previous_version
                continue

            # Apply in transaction (each migration independently)
            try:
                with transaction.atomic():
                    self._test_rollback(questionnaires, migration, current_version, previous_version)
                    self._apply_rollback(questionnaires, migration)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Rollback {migration_num} complete: {record_count} record(s) rolled back to {previous_version}\n"
                    )
                )
                current_version = previous_version
            except Exception as e:
                raise CommandError(
                    f"Rollback {migration_num} failed:\n{str(e)}\n"
                    f"Records remain at version {current_version}. "
                    f"Fix the issue and retry with: python manage.py schema_rollback_questionnaire {migration_number}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Successfully rolled back to version {target_version}"
            )
        )

    def _test_rollback(self, questionnaires, migration, from_version, to_version):
        """Validate all rollback transforms before applying.

        Args:
            questionnaires: List of Questionnaire objects
            migration: Migration module with migrate_backward() function
            from_version: Current schema version before rollback
            to_version: Target schema version after rollback

        Raises:
            CommandError: If validation fails for any record
        """
        # For rollback, target_schema is the one we roll back FROM
        # previous_schema is the one we roll back TO
        from_schema = migration.target_schema()
        to_schema = migration.previous_schema()

        success_count = 0
        failed_records = []

        for questionnaire in questionnaires:
            doc = questionnaire.document

            # Apply rollback transform
            try:
                transformed = deepcopy(doc)
                transformed = migration.migrate_backward(transformed)

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
        self.stdout.write(f"Validated {success_count}/{len(questionnaires)}")

        if failed_records:
            errors = "\n".join(
                [f"  - Record {rec_id}: {err}" for rec_id, err in failed_records]
            )
            raise CommandError(
                f"Validation failed for {len(failed_records)} record(s):\n{errors}"
            )

    def _apply_rollback(self, questionnaires, migration):
        """Apply rollback transformation to all records (called within transaction).

        Args:
            questionnaires: List of Questionnaire objects
            migration: Migration module with migrate_backward() function
        """
        for questionnaire in questionnaires:
            doc = questionnaire.document
            doc = migration.migrate_backward(doc)
            questionnaire.document = doc
            questionnaire.save(update_fields=["document"])
