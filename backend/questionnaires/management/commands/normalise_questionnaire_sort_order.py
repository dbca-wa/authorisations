from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber

from questionnaires.models import Questionnaire


class Command(BaseCommand):
    help = (
        "Normalise Questionnaire.sort_order globally so latest versions have "
        "contiguous visible ranks (1..N) and historical versions are set to 0. "
        "Safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be updated without applying changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        to_update = []

        latest_rows = list(
            Questionnaire.objects.annotate(
                _latest_rank=Window(
                    expression=RowNumber(),
                    partition_by=[F("process_id"), F("code")],
                    order_by=F("version").desc(),
                )
            )
            .filter(_latest_rank=1)
            .order_by("sort_order", "process_id", "code", "-version", "-id")
        )

        # Preserve the current visible global order, but compact it to 1..N.
        for visible_rank, latest_row in enumerate(latest_rows, start=1):
            if latest_row.sort_order != visible_rank:
                latest_row.sort_order = visible_rank
                to_update.append(latest_row)

        # Set all historical versions to 0 so they never compete in visible ordering.
        historical_rows = Questionnaire.objects.exclude(id__in=[row.id for row in latest_rows])
        for row in historical_rows:
            if row.sort_order != 0:
                row.sort_order = 0
                to_update.append(row)

        updated_total = len(to_update)
        if to_update and not dry_run:
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
