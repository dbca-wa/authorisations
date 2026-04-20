# Generated manually to finalise questionnaire code backfill constraints.

import django.db.models.deletion
from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        (
            "questionnaires",
            "0004_backfill_questionnaire_code_from_name",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="questionnaire",
            name="code",
            field=models.SlugField(
                blank=False,
                db_index=True,
                help_text="Stable questionnaire code used to identify a version lineage within a process.",
                max_length=20,
                null=False,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="questionnaire",
            name="qnaire_unique_process_name_version_desc",
        ),
        migrations.AddConstraint(
            model_name="questionnaire",
            constraint=models.UniqueConstraint(
                models.F("process"),
                models.F("code"),
                models.OrderBy(models.F("version"), descending=True),
                name="qnaire_unique_process_code_version_desc",
            ),
        ),
        migrations.AlterModelOptions(
            name="questionnaire",
            options={"ordering": ("process_id", "code", "-version")},
        ),
        # the new `updated_at` and `updated_by` fields are added
        migrations.AddField(
            model_name='questionnaire',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='updated_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_questionnaires', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='name',
            field=models.CharField(help_text='The display name of the questionnaire such as; "New application", "Renewal" etc.', max_length=100),
        ),
    ]
