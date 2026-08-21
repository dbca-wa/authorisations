"""Management command to show current schema status for questionnaires.

Usage:
    python manage.py schema_status_questionnaire

Shows:
    - Current schema version (from code)
    - Distribution of records by schema_version
    - Available migrations
    - Warnings for mixed-version databases (error state)
"""

from collections import Counter
from django.core.management.base import BaseCommand

from questionnaires.models import Questionnaire
from questionnaires.schema import SCHEMA_VERSION
from questionnaires.schema_migrations_loader import list_migrations
from questionnaires.schema_migration_utils import get_db_schema_version


class Command(BaseCommand):
    """Display current schema migration status."""

    help = "Show current schema version and record distribution"

    def handle(self, **options):
        """Display schema status.

        Shows current code version, database distribution by schema_version,
        available migrations, and warnings for error states (mixed versions).
        """
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Schema Migration Status")
        self.stdout.write("=" * 70 + "\n")

        # Current code version
        self.stdout.write(f"Code schema version: {SCHEMA_VERSION}")

        # Database version (try to get, but handle mixed gracefully)
        try:
            db_version = get_db_schema_version()
        except RuntimeError:
            # Mixed versions - status command is diagnostic, so show it
            db_version = None

        self.stdout.write(f"Database schema version: {db_version or 'MIXED/EMPTY'}\n")

        # Record distribution
        self.stdout.write("Record distribution:")
        distribution = self._get_distribution()

        if not distribution:
            self.stdout.write("  (no records in database)")
        else:
            for version, count in sorted(distribution.items()):
                marker = " ✓" if version == SCHEMA_VERSION else ""
                self.stdout.write(f"  {version}: {count}{marker}")

        # Warnings
        if len(distribution) > 1:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  MIXED STATE: Records at {len(distribution)} different versions!"
                )
            )
            self.stdout.write(
                "  This may indicate a failed migration. "
                "Contact support or manually review database state.\n"
            )

        # Available migrations
        self.stdout.write("\nAvailable migrations:")
        migrations = list_migrations()
        if not migrations:
            self.stdout.write("  (no migrations defined)")
        else:
            for migration in migrations:
                self.stdout.write(f"  {migration}")

        self.stdout.write("\n" + "=" * 70 + "\n")

    def _get_distribution(self) -> dict:
        """Get distribution of records by schema_version.

        Returns:
            Dictionary mapping schema_version to record count.
            Returns empty dict if no records in database.
        """
        records = Questionnaire.objects.all()

        if not records.exists():
            return {}

        # Extract schema_version from each document JSON field
        versions = []
        for record in records:
            version = record.document.get("schema_version")
            versions.append(version)

        return dict(Counter(versions))
