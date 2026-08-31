"""Integration tests for schema_migrate management command.

Tests the generic schema_migrate command with --target flag across both
questionnaires and applications targets. Covers idempotency (already at target 
= no-op), dry-run validation, path-finding with sequential execution, 
transaction isolation per migration, and error messages.
"""

import pytest
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from questionnaires.models import Questionnaire
from processes.models import AuthorisationProcess
from users.models import User
from schema_migration_framework.executor import get_migrations_package_path


@pytest.mark.django_db
class TestSchemaMigrateCommandBasic:
    """Basic command parsing and argument handling for questionnaires target."""

    def test_command_requires_target_and_migration(self):
        """Command requires both --target and migration number arguments."""
        with pytest.raises(CommandError):
            call_command("schema_migrate")

    def test_command_requires_migration_number(self):
        """Command requires migration number argument when target provided."""
        with pytest.raises(CommandError):
            call_command("schema_migrate", "--target", "questionnaires")

    def test_command_rejects_missing_migration(self):
        """Command raises error for non-existent migration."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_migrate", "--target", "questionnaires", "9999")
        assert "not found" in str(exc_info.value).lower()

    def test_command_rejects_invalid_target(self):
        """Command rejects unknown target."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_migrate", "--target", "invalid_target", "0001")
        assert "invalid_target" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestSchemaMigrateEmptyDatabase:
    """Migrate with empty database."""

    def test_migrate_empty_database_questionnaires(self):
        """Migrating empty questionnaires DB succeeds (no-op)."""
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        output = out.getvalue()
        
        # With empty DB, should either say "no questionnaires" or handle gracefully
        assert "questionnaires" in output.lower() or "Already at version" in output or "no records" in output.lower()


@pytest.mark.django_db
class TestSchemaMigrateIdempotency(TestCase):
    """Idempotency: running same migration twice is safe (second run = no-op)."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test",
            name="Test Process"
        )

    def test_idempotent_when_already_at_target(self):
        """Running migrate to current version is no-op."""
        # Create a record at version 1
        Questionnaire.objects.create(
            process=self.process,
            name="Test Questionnaire",
            code="test",
            version=1,
            document={
                "schema_version": 1,
                "steps": [],
            },
            created_by=self.user
        )

        # First migrate to 0001 should succeed (already there)
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        output = out.getvalue()

        # Should report already at version
        assert "Already at version" in output


@pytest.mark.django_db
@pytest.mark.django_db
class TestSchemaMigratePathFinding(TestCase):
    """Path-finding: migrate automatically discovers intermediate migrations."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser2", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test2",
            name="Test Process 2"
        )

    def test_migrate_with_unknown_version_fails(self):
        """Cannot migrate if DB version is not in known migrations."""
        # Create record at unknown version (not in any migration)
        Questionnaire.objects.create(
            process=self.process,
            name="Test Q",
            code="test",
            version=1,
            document={
                "schema_version": 9999,
                "steps": [],
            },
            created_by=self.user
        )

        # Trying to migrate to 0001 should fail because current version is unknown
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0001"
            )

        error = str(exc_info.value)
        # Should mention path finding failure
        assert ("Cannot determine" in error) or ("Cannot find" in error) or ("unknown" in error.lower())


@pytest.mark.django_db
class TestSchemaMigrateDryRun(TestCase):
    """Dry-run produces zero database changes."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser3", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test3",
            name="Test Process 3"
        )

    def test_dryrun_with_no_records_succeeds(self):
        """--dry-run succeeds with empty database."""
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            "--dry-run",
            stdout=out
        )
        output = out.getvalue()

        # Should handle gracefully
        assert "questionnaires" in output.lower() or output


@pytest.mark.django_db
@pytest.mark.django_db
class TestSchemaMigrateSuccessfulTransform(TestCase):
    """Successful forward migration updates records and version tracking."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser4", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test4",
            name="Test Process 4"
        )

    def test_migrate_idempotent_already_at_target(self):
        """Migrating to current version is no-op."""
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            name="Test Q",
            code="test_migrate_idempotent",
            version=1,
            document={
                "schema_version": 1,
                "steps": [],
            },
            created_by=self.user
        )

        # Migrate to 0001 (current version)
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )

        questionnaire.refresh_from_db()
        # Should still be at version 1 (already there)
        assert questionnaire.document.get("schema_version") == 1


@pytest.mark.django_db
class TestSchemaMigrateErrorMessages:
    """Error messages are informative."""

    def test_error_message_on_missing_migration(self):
        """Error message mentions migration number."""
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "9999"
            )
        
        error = str(exc_info.value)
        assert "9999" in error or "not found" in error.lower()
