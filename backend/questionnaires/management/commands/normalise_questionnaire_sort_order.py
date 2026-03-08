from django.core.management.base import BaseCommand
from django.db import transaction

from questionnaires.models import Questionnaire


class Command(BaseCommand):
    help = (
        "Normalise Questionnaire.sort_order values per process to contiguous positive "
        "integers. Safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be updated without applying changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated_total = 0

        process_ids = (
            Questionnaire.objects.values_list("process_id", flat=True)
            .distinct()
            .order_by("process_id")
        )

        for process_id in process_ids:
            rows = list(
                Questionnaire.objects.filter(process_id=process_id).order_by(
                    "sort_order", "name", "-version", "id"
                )
            )

            to_update = []
            for index, row in enumerate(rows, start=1):
                if row.sort_order != index:
                    row.sort_order = index
                    to_update.append(row)

            if to_update:
                updated_total += len(to_update)
                if not dry_run:
                    with transaction.atomic():
                        Questionnaire.objects.bulk_update(to_update, ["sort_order"])

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run complete. Rows requiring normalisation: {updated_total}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Normalisation complete. Rows updated: {updated_total}"
                )
            )
