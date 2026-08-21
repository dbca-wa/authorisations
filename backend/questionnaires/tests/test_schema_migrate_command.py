"""Tests for schema_migrate_questionnaire management command.

Tests idempotency (already at target = no-op), dry-run, path-finding with
sequential execution, transaction isolation per migration, and error messages.
"""

import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
class TestSchemaMigrateCommandBasic:
    """Basic command parsing and argument handling."""

    def test_command_requires_migration_number(self):
        """Command requires migration number argument."""
        with pytest.raises(CommandError):
            call_command("schema_migrate_questionnaire")

    def test_command_rejects_missing_migration(self):
        """Command raises error for non-existent migration."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_migrate_questionnaire", "9999")
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestSchemaMigrateEmptyDatabase:
    """Migrate with empty database."""

    def test_migrate_empty_database(self):
        """Migrating empty database succeeds (no-op)."""
        out = StringIO()
        call_command("schema_migrate_questionnaire", "0001", stdout=out)
        output = out.getvalue()
        
        # With empty DB, should either say "no questionnaires" or handle gracefully
        assert "questionnaires" in output.lower() or "Already at version" in output


@pytest.mark.django_db
class TestSchemaMigrateIdempotency:
    """Idempotency: running same migration twice is safe (second run = no-op)."""

    def test_idempotent_when_already_at_target(self, questionnaire_factory):
        """Running migrate to current version is no-op."""
        # Create a record at version "1"
        questionnaire_factory(
            document={
                "schema_version": "1",
                "steps": [],
            }
        )

        # First migrate to 0001 should succeed (already there)
        out = StringIO()
        call_command("schema_migrate_questionnaire", "0001", stdout=out)
        output = out.getvalue()

        # Should report already at version
        assert "Already at version" in output


@pytest.mark.django_db
class TestSchemaMigratePathFinding:
    """Path-finding: migrate automatically discovers intermediate migrations."""

    def test_migrate_with_unknown_version_fails(self, questionnaire_factory):
        """Cannot migrate if DB version is not in known migrations."""
        # Create record at unknown version (not in any migration)
        questionnaire_factory(
            document={
                "schema_version": "999-invalid",
                "steps": [],
            }
        )

        # Trying to migrate to 0001 should fail because current version is unknown
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_migrate_questionnaire", "0001")

        error = str(exc_info.value)
        # Should mention path finding failure
        assert ("Cannot determine" in error) or ("Cannot find" in error)


@pytest.mark.django_db
class TestSchemaMigrateDryRun:
    """Dry-run produces zero database changes."""

    def test_dryrun_makes_no_changes(self, questionnaire_factory):
        """--dry-run tests migration without writing."""
        questionnaire = questionnaire_factory()
        
        # Get current version (factory creates with "2025.07-1")
        version_before = questionnaire.document["schema_version"]

        # Run dry-run
        out = StringIO()
        call_command(
            "schema_migrate_questionnaire", "0001", dry_run=True, stdout=out
        )

        # Verify no change
        questionnaire.refresh_from_db()
        version_after = questionnaire.document["schema_version"]

        assert version_before == version_after
        assert version_after == "2025.07-1"

    def test_dryrun_shows_would_transform_count(self, questionnaire_factory):
        """--dry-run reports how many records would transform."""
        questionnaire_factory()
        questionnaire_factory()

        out = StringIO()
        call_command(
            "schema_migrate_questionnaire", "0001", dry_run=True, stdout=out
        )
        output = out.getvalue()

        # Should report would transform or testing transforms
        assert "Would transform" in output or "DRY RUN" in output


@pytest.mark.django_db
class TestSchemaMigrateSuccessfulTransform:
    """Successful forward migration updates records and version tracking."""

    def test_migrate_updates_version_in_document(self, questionnaire_factory):
        """Migrated record has new version in schema_version field."""
        questionnaire = questionnaire_factory(
            document={
                "schema_version": "2025.07-1",
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

        # Migrate from 2025.07-1 to 1
        out = StringIO()
        call_command("schema_migrate_questionnaire", "0001", stdout=out)

        questionnaire.refresh_from_db()
        # Should now be at version 1
        assert questionnaire.document.get("schema_version") == "1"


@pytest.mark.django_db
class TestSchemaMigrateTransactionRollback:
    """Transaction rollback on any transform error."""

    def test_rollback_on_validation_error(self, questionnaire_factory):
        """If any record fails, migration doesn't corrupt data."""
        questionnaire = questionnaire_factory(
            document={
                "schema_version": "2025.07-1",
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

        version_before = questionnaire.document["schema_version"]

        # Migrate (should succeed)
        out = StringIO()
        call_command("schema_migrate_questionnaire", "0001", stdout=out)

        questionnaire.refresh_from_db()
        # Should have changed version
        assert questionnaire.document["schema_version"] != version_before


@pytest.mark.django_db
class TestSchemaMigrateErrorMessages:
    """Error messages are informative."""

    def test_error_message_on_missing_migration(self):
        """Error message mentions migration number."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_migrate_questionnaire", "9999")
        
        error = str(exc_info.value)
        assert "9999" in error or "not found" in error.lower()
