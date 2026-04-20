# Generated manually to backfill questionnaire code values from legacy names.

from django.db import migrations, models
from django.utils.text import slugify


def _code_base_from_name(name: str) -> str:
    """Build a three-letter lowercase code base from the questionnaire name."""
    slug = slugify(name or "")
    first_word = slug.split("-")[0] if slug else ""
    base = (first_word[:3] or "q").lower()
    return base


def backfill_questionnaire_code_from_name(apps, schema_editor):
    """Populate code from name while preserving deterministic uniqueness per process."""
    Questionnaire = apps.get_model("questionnaires", "Questionnaire")

    rows = list(
        Questionnaire.objects.all().order_by("process_id", "name", "id")
    )

    # Keep one code per historical lineage, then reuse it for all versions.
    code_by_lineage = {}
    used_codes_by_process = {}

    for row in rows:
        process_id = row.process_id
        lineage_key = (process_id, (row.name or "").strip().casefold())

        if lineage_key in code_by_lineage:
            row.code = code_by_lineage[lineage_key]
            continue

        base_code = _code_base_from_name(row.name)
        used_codes = used_codes_by_process.setdefault(process_id, set())

        candidate = base_code
        suffix = 2
        while candidate in used_codes:
            candidate = f"{base_code}{suffix}"
            suffix += 1

        code_by_lineage[lineage_key] = candidate
        used_codes.add(candidate)
        row.code = candidate

    Questionnaire.objects.bulk_update(rows, ["code"])


def reverse_backfill_questionnaire_code_from_name(apps, schema_editor):
    """Reverse the backfill by clearing generated code values."""
    Questionnaire = apps.get_model("questionnaires", "Questionnaire")
    Questionnaire.objects.all().update(code=None)


class Migration(migrations.Migration):

    dependencies = [
        (
            "questionnaires",
            "0003_remove_questionnaire_qnaire_unique_slug_version_desc_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnaire",
            name="code",
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text="Stable questionnaire code used to identify a version lineage within a process.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(
            backfill_questionnaire_code_from_name,
            reverse_backfill_questionnaire_code_from_name,
        ),
    ]
