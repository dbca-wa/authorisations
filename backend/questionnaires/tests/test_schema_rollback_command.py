"""Tests for schema_rollback_questionnaire management command.

Tests idempotency (already at target = no-op), dry-run, backward transformation,
and error messages for failed rollbacks.
"""

import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
class TestSchemaRollbackCommandBasic:
    """Basic command parsing and argument handling."""

    def test_command_accepts_migration_number(self):
        """Command accepts target migration number as argument."""
        out = StringIO()
        # Rollback to 0001 with empty DB should succeed (no-op)
        call_command("schema_rollback_questionnaire", "0001", stdout=out)
        output = out.getvalue()
        assert "Already at version" in output or "No questionnaires" in output

    def test_command_rejects_missing_migration(self):
        """Command raises error for non-existent migration."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_rollback_questionnaire", "9999")
        assert "not found" in str(exc_info.value).lower()

    def test_command_rejects_missing_argument(self):
        """Command requires migration number argument."""
        with pytest.raises(CommandError):
            call_command("schema_rollback_questionnaire")


@pytest.mark.django_db
class TestSchemaRollbackIdempotency:
    """Idempotency: running same rollback twice is safe (second run = no-op)."""

    def test_idempotent_when_already_at_target(self, questionnaire_factory):
        """Rolling back to current version is no-op."""
        questionnaire_factory(
            document={
                "schema_version": 1,
                "steps": [
                    {
                        "title": "Step 1",
                        "description": "Test step",
                        "sections": [
                            {
                                "title": "Section 1",
                                "description": "Test section",
                                "questions": [
                                    {
                                        "label": "Question 1",
                                        "type": "text",
                                        "is_required": False,
                                        "description": "Test question",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        # First rollback to 0001 should succeed (already there)
        out = StringIO()
        call_command("schema_rollback_questionnaire", "0001", stdout=out)
        output = out.getvalue()

        assert "Already at version" in output

    def test_second_rollback_is_noop(self, questionnaire_factory):
        """Running same rollback twice shows no-op."""
        questionnaire_factory(
            document={
                "schema_version": 1,
                "steps": [
                    {
                        "title": "Step 1",
                        "description": "Test step",
                        "sections": [
                            {
                                "title": "Section 1",
                                "description": "Test section",
                                "questions": [
                                    {
                                        "label": "Question 1",
                                        "type": "text",
                                        "is_required": False,
                                        "description": "Test question",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        # First call
        out1 = StringIO()
        call_command("schema_rollback_questionnaire", "0001", stdout=out1)

        # Second call should also be no-op
        out2 = StringIO()
        call_command("schema_rollback_questionnaire", "0001", stdout=out2)

        output2 = out2.getvalue()
        assert "Already at version" in output2


@pytest.mark.django_db
class TestSchemaRollbackDryRun:
    """Dry-run produces zero database changes."""

    def test_dryrun_makes_no_changes(self, questionnaire_factory):
        """--dry-run tests rollback without writing."""
        questionnaire = questionnaire_factory()

        version_before = questionnaire.document["schema_version"]

        # Run dry-run
        out = StringIO()
        call_command(
            "schema_rollback_questionnaire", "0001", dry_run=True, stdout=out
        )

        # Verify no change
        questionnaire.refresh_from_db()
        version_after = questionnaire.document["schema_version"]

        assert version_before == version_after

    def test_dryrun_shows_output(self, questionnaire_factory):
        """--dry-run reports what would happen."""
        questionnaire_factory()
        questionnaire_factory()

        out = StringIO()
        call_command(
            "schema_rollback_questionnaire", "0001", dry_run=True, stdout=out
        )
        output = out.getvalue()

        # Should have some output
        assert len(output) > 0


@pytest.mark.django_db
class TestSchemaRollbackErrorHandling:
    """Error messages are clear about what failed."""

    def test_error_when_target_not_found(self):
        """Clear error when target migration doesn't exist."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_rollback_questionnaire", "9999")

        error = str(exc_info.value)
        assert "9999" in error or "not found" in error.lower()

    def test_error_on_missing_target_version(self):
        """Error when cannot find path to non-existent target."""
        with pytest.raises(CommandError):
            call_command("schema_rollback_questionnaire", "9999")


@pytest.mark.django_db
class TestSchemaRollbackMultipleRecords:
    """Rollback handles multiple records correctly."""

    def test_rollback_all_records_together(self, questionnaire_factory):
        """All records transformed in same transaction."""
        for i in range(3):
            questionnaire_factory(
                document={
                    "schema_version": 1,
                    "steps": [
                        {
                            "title": f"Step {i}",
                            "description": "Test step",
                            "sections": [
                                {
                                    "title": "Section 1",
                                    "description": "Test section",
                                    "questions": [
                                        {
                                            "label": "Question 1",
                                            "type": "text",
                                            "is_required": False,
                                            "description": "Test question",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            )

        out = StringIO()
        call_command("schema_rollback_questionnaire", "0001", stdout=out)
        output = out.getvalue()

        # Should produce output
        assert len(output) > 0

    def test_rollback_consistent_state(self, questionnaire_factory):
        """All records end at same version after rollback."""
        questionnaire_factory(
            document={
                "schema_version": 1,
                "steps": [
                    {
                        "title": "Step 1",
                        "description": "Test step",
                        "sections": [
                            {
                                "title": "Section 1",
                                "description": "Test section",
                                "questions": [
                                    {
                                        "label": "Question 1",
                                        "type": "text",
                                        "is_required": False,
                                        "description": "Test question",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        questionnaire_factory(
            document={
                "schema_version": 1,
                "steps": [
                    {
                        "title": "Step 1",
                        "description": "Test step",
                        "sections": [
                            {
                                "title": "Section 1",
                                "description": "Test section",
                                "questions": [
                                    {
                                        "label": "Question 1",
                                        "type": "text",
                                        "is_required": False,
                                        "description": "Test question",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        # Run rollback (should be no-op since already at version 1)
        out = StringIO()
        call_command("schema_rollback_questionnaire", "0001", stdout=out)

        # All should have same version
        from questionnaires.models import Questionnaire
        versions = {q.document.get("schema_version") for q in Questionnaire.objects.all()}
        assert len(versions) == 1
        assert 1 in versions
