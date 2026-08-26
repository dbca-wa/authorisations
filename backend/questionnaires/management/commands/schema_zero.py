"""Temporary manual recovery utility: unconditionally set schema_version to 0 or '2025.07-1'.

Emergency-only tool for manual rollback scenarios where the migration framework cannot
be used. This command forcibly sets schema_version on all questionnaires without validation.
Use only under guidance from development team.

Normal workflow: Use schema_migrate_questionnaire and schema_rollback_questionnaire.
Manual recovery: Use this command if migrations are blocked or data is inconsistent.
"""

from django.core.management.base import BaseCommand

from questionnaires.models import Questionnaire


class Command(BaseCommand):
    """Unconditionally set schema_version on all questionnaires.

    This is a temporary emergency recovery tool, NOT part of normal migration workflow.
    """

    help = "[EMERGENCY ONLY] Unconditionally set schema_version to 0 or '2025.07-1'"

    def add_arguments(self, parser):
        """Add --revert flag to toggle direction."""
        parser.add_argument(
            "--revert",
            action="store_true",
            help='Revert: unconditionally set all schema_version to "2025.07-1" (backward)',
        )

    def handle(self, revert=False, **options):
        """Execute unconditional schema_version conversion.

        Forward (default): Set all questionnaires to schema_version 0 (integer).
        Backward (--revert): Set all questionnaires to schema_version "2025.07-1" (string).

        This bypasses all validation and idempotency checks. Use only for emergency
        manual recovery when migration framework cannot be used.
        """
        questionnaires = Questionnaire.objects.all()
        count = 0

        if revert:
            # BACKWARD: Unconditionally set to "2025.07-1" (string)
            target_version = "2025.07-1"
            direction = "0 → '2025.07-1'"
            for q in questionnaires:
                q.document["schema_version"] = target_version
                q.save()
                count += 1
        else:
            # FORWARD: Unconditionally set to 0 (integer)
            target_version = 0
            direction = "(any) → 0"
            for q in questionnaires:
                q.document["schema_version"] = target_version
                q.save()
                count += 1

        self.stdout.write(
            self.style.WARNING(
                f"[EMERGENCY] Unconditionally converted {count} records: {direction}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "⚠️  This command bypasses validation. Verify data consistency after use."
            )
        )
