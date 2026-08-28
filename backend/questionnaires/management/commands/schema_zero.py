"""Temporary manual recovery utility: unconditionally set schema_version to 0 or calendar version.

Emergency-only tool for manual rollback scenarios where the migration framework cannot
be used. This command forcibly sets schema_version on all records of a target without validation.
Use only under guidance from development team.

Normal workflow: Use schema_migrate and schema_rollback with --target flag.
Manual recovery: Use this command if migrations are blocked or data is inconsistent.

Supported Targets:
  - questionnaires: Reset to 0 (forward) or "2025.07-1" (backward with --revert)
  - applications: Reset to 0 (forward) or "2025.09-1" (backward with --revert)
"""

from django.core.management.base import BaseCommand, CommandError

from questionnaires.models import Questionnaire
from applications.models import Application


# Target configuration: maps target name to model, backward version
_TARGET_CONFIG = {
    "questionnaires": {
        "model": Questionnaire,
        "backward_version": "2025.07-1",
    },
    "applications": {
        "model": Application,
        "backward_version": "2025.09-1",
    },
}


class Command(BaseCommand):
    """Unconditionally set schema_version on records for a specified target.

    This is a temporary emergency recovery tool, NOT part of normal migration workflow.
    """

    help = "[EMERGENCY ONLY] Unconditionally set schema_version to 0 or calendar version per target"

    def add_arguments(self, parser):
        """Add --target (mandatory) and --revert flags."""
        parser.add_argument(
            "--target",
            required=True,
            choices=list(_TARGET_CONFIG.keys()),
            help="Target to reset: questionnaires or applications (MANDATORY)",
        )
        parser.add_argument(
            "--revert",
            action="store_true",
            help="Revert: set schema_version to calendar version (backward)",
        )

    def handle(self, target, revert=False, **options):
        """Execute unconditional schema_version conversion for specified target.

        Forward (default): Set all records to schema_version 0 (integer).
        Backward (--revert): Set all records to target's calendar version (string).

        This bypasses all validation and idempotency checks. Use only for emergency
        manual recovery when migration framework cannot be used.
        """
        if target not in _TARGET_CONFIG:
            raise CommandError(
                f"Unknown target: {target}. Supported targets: {', '.join(_TARGET_CONFIG.keys())}"
            )

        config = _TARGET_CONFIG[target]
        model = config["model"]
        backward_version = config["backward_version"]

        records = model.objects.all()
        count = 0

        if revert:
            # BACKWARD: Unconditionally set to calendar version (string)
            target_version = backward_version
            direction = f"(any) → '{backward_version}'"
            for record in records:
                record.document["schema_version"] = target_version
                record.save()
                count += 1
        else:
            # FORWARD: Unconditionally set to 0 (integer)
            target_version = 0
            direction = f"(any) → 0"
            for record in records:
                record.document["schema_version"] = target_version
                record.save()
                count += 1

        self.stdout.write(
            self.style.WARNING(
                f"[EMERGENCY] {target}: Unconditionally converted {count} records: {direction}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "⚠️  This command bypasses validation. Verify data consistency after use."
            )
        )
