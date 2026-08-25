"""Temporary migration utility: convert schema_version between '2025.07-1' and 0."""

from django.core.management.base import BaseCommand

from questionnaires.models import Questionnaire


class Command(BaseCommand):
    help = "Convert schema_version between '2025.07-1' (string) and 0 (integer)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--revert",
            action="store_true",
            help='Revert: convert integer 0 back to string "2025.07-1"',
        )

    def handle(self, revert=False, **options):
        if revert:
            # Convert integer 0 → string "2025.07-1"
            questionnaires = Questionnaire.objects.all()
            count = 0
            for q in questionnaires:
                if q.document.get("schema_version") == 0:
                    q.document["schema_version"] = "2025.07-1"
                    q.save()
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Converted {count} records: 0 → '2025.07-1'")
            )
        else:
            # Convert string "2025.07-1" → integer 0
            questionnaires = Questionnaire.objects.all()
            count = 0
            for q in questionnaires:
                if q.document.get("schema_version") == "2025.07-1":
                    q.document["schema_version"] = 0
                    q.save()
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Converted {count} records: '2025.07-1' → 0")
            )
