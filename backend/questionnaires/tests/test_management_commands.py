"""Tests for questionnaire management commands."""

from io import StringIO

import pytest
from django.core.management import call_command

from questionnaires.models import Questionnaire


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _document():
    """Return a minimal valid questionnaire document payload for command tests."""
    return {
        "schema_version": "2025.07-1",
        "steps": [
            {
                "title": "Step 1",
                "description": "",
                "sections": [
                    {
                        "title": "Section 1",
                        "description": "",
                        "questions": [
                            {
                                "label": "Question 1",
                                "type": "text",
                                "is_required": False,
                                "description": "",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _create_questionnaire(*, process, user, code: str, version: int, sort_order: int):
    """Create a questionnaire row with the minimum fields needed for ordering tests."""
    return Questionnaire.objects.create(
        process=process,
        code=code,
        name=f"{code} v{version}",
        description="Description",
        version=version,
        document=_document(),
        sort_order=sort_order,
        created_by=user,
    )


def test_normalise_questionnaire_sort_order_dry_run_reports_without_changes(process, user):
    """Keep questionnaire rows untouched when the command is run in dry-run mode."""
    latest_new = _create_questionnaire(process=process, user=user, code="new", version=2, sort_order=30)
    _create_questionnaire(process=process, user=user, code="new", version=1, sort_order=9)
    latest_renewal = _create_questionnaire(process=process, user=user, code="renewal", version=3, sort_order=10)
    _create_questionnaire(process=process, user=user, code="renewal", version=2, sort_order=4)
    latest_extension = _create_questionnaire(process=process, user=user, code="extension", version=1, sort_order=20)

    stdout = StringIO()

    call_command("normalise_questionnaire_sort_order", dry_run=True, stdout=stdout)

    latest_new.refresh_from_db()
    latest_renewal.refresh_from_db()
    latest_extension.refresh_from_db()

    assert latest_new.sort_order == 30
    assert latest_renewal.sort_order == 10
    assert latest_extension.sort_order == 20
    assert "Rows requiring normalisation: 5" in stdout.getvalue()


def test_normalise_questionnaire_sort_order_compacts_latest_rows_and_zeros_history(process, user):
    """Rebuild visible questionnaire ordering while pushing historical versions out of view."""
    latest_new = _create_questionnaire(process=process, user=user, code="new", version=2, sort_order=30)
    historical_new = _create_questionnaire(process=process, user=user, code="new", version=1, sort_order=9)
    latest_renewal = _create_questionnaire(process=process, user=user, code="renewal", version=3, sort_order=10)
    historical_renewal = _create_questionnaire(process=process, user=user, code="renewal", version=2, sort_order=4)
    latest_extension = _create_questionnaire(process=process, user=user, code="extension", version=1, sort_order=20)

    stdout = StringIO()

    call_command("normalise_questionnaire_sort_order", stdout=stdout)

    latest_new.refresh_from_db()
    historical_new.refresh_from_db()
    latest_renewal.refresh_from_db()
    historical_renewal.refresh_from_db()
    latest_extension.refresh_from_db()

    assert [latest_new.sort_order, latest_extension.sort_order, latest_renewal.sort_order] == [3, 2, 1]
    assert historical_new.sort_order == 0
    assert historical_renewal.sort_order == 0
    assert "Normalisation complete. Rows updated: 5" in stdout.getvalue()


def test_normalise_questionnaire_sort_order_is_idempotent(process, user):
    """Leave questionnaire sort_order unchanged on a second normalisation pass."""
    _create_questionnaire(process=process, user=user, code="new", version=2, sort_order=30)
    _create_questionnaire(process=process, user=user, code="new", version=1, sort_order=9)
    _create_questionnaire(process=process, user=user, code="renewal", version=3, sort_order=10)
    _create_questionnaire(process=process, user=user, code="renewal", version=2, sort_order=4)
    _create_questionnaire(process=process, user=user, code="extension", version=1, sort_order=20)

    first_stdout = StringIO()
    second_stdout = StringIO()

    call_command("normalise_questionnaire_sort_order", stdout=first_stdout)
    call_command("normalise_questionnaire_sort_order", stdout=second_stdout)

    assert "Rows updated: 5" in first_stdout.getvalue()
    assert "Rows updated: 0" in second_stdout.getvalue()
    assert list(Questionnaire.objects.order_by("process_id", "code", "-version").values_list("sort_order", flat=True)) == [2, 3, 0, 1, 0]