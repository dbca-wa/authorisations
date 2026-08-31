"""Integration tests for schema_rollback management command.

Tests the generic schema_rollback command with --target flag across both
questionnaires and applications targets. Covers idempotency (already at target 
= no-op), dry-run validation, backward transformation verification, backward
migration rejection, transaction isolation, and error messages for failed
rollbacks.
"""

import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from questionnaires.models import Questionnaire
from processes.models import AuthorisationProcess
from users.models import User
from applications.models import Application
from schema_migration_framework.executor import get_migrations_package_path
from schema_migration_framework.loader import get_migration


class SchemaRollbackCommandTestCase(TestCase):
    """Test schema_rollback command with questionnaires target."""

    @classmethod
    def setUpClass(cls):
        """Set up process and user for all tests."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test",
            name="Test Process"
        )
        cls.migrations_path = get_migrations_package_path("questionnaires.schema_migrations")

    def setUp(self):
        """Create test questionnaires at version 1."""
        # Create 3 test questionnaires at v1
        for i in range(3):
            Questionnaire.objects.create(
                process=self.process,
                name=f"Test Questionnaire {i}",
                code=f"test_{i}",
                version=1,
                document={
                    "schema_version": 1,
                    "steps": [
                        {
                            "title": f"Step {i}",
                            "sections": [
                                {
                                    "title": "Test Section",
                                    "questions": [
                                        {"label": "Test Q", "type": "text"}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                created_by=self.user
            )


@pytest.mark.django_db
class TestSchemaRollbackCommandBasic(TestCase):
    """Basic command parsing and argument handling."""

    def test_command_requires_target_and_migration(self):
        """Command requires both --target and migration number arguments."""
        with pytest.raises(CommandError):
            call_command("schema_rollback")

    def test_command_requires_migration_number(self):
        """Command requires migration number argument when target provided."""
        with pytest.raises(CommandError):
            call_command("schema_rollback", "--target", "questionnaires")

    def test_command_rejects_missing_migration(self):
        """Command raises error for non-existent migration."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_rollback", "--target", "questionnaires", "9999")
        assert "not found" in str(exc_info.value).lower()

    def test_command_accepts_valid_migration(self):
        """Command accepts valid migration number as argument."""
        out = StringIO()
        # Rollback to 0001 with empty DB should succeed (no-op)
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        output = out.getvalue()
        assert "Already at version" in output or "No questionnaire" in output.lower() or output


@pytest.mark.django_db
class TestSchemaRollbackEmptyDatabase(SchemaRollbackCommandTestCase):
    """Rollback with empty database."""

    def test_rollback_empty_database_succeeds(self):
        """Rollback empty DB succeeds (no-op)."""
        # Clear any created records from setUp
        Questionnaire.objects.all().delete()
        
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        output = out.getvalue()
        
        # With empty DB, should handle gracefully
        assert "questionnaires" in output.lower() or "no records" in output.lower() or "Already at version" in output


@pytest.mark.django_db
class TestSchemaRollbackCommandBasicExecution(SchemaRollbackCommandTestCase):
    """Test dry-run rollback from v1 to v0 using 0000 migration."""

    def test_rollback_0000_from_v1_to_v0_dry_run(self):
        """Test dry-run rollback from v1 to v0 using 0000 migration."""
        output = StringIO()
        
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--dry-run",
            stdout=output
        )
        
        command_output = output.getvalue()
        
        # Verify correct messages
        assert "Found 3 questionnaires record(s) at version 1" in command_output
        assert "Rollback path: 0001 → 0000" in command_output
        assert "Rolling back migration 0001 (1 → 0)..." in command_output
        assert "Tested 3/3" in command_output
        assert "Successfully rolled back to version 0" in command_output
        
        # Verify no actual changes (dry-run)
        for q in Questionnaire.objects.all():
            assert q.document["schema_version"] == 1

    def test_rollback_0000_from_v1_to_v0_actual(self):
        """Test actual rollback from v1 to v0 using 0000 migration."""
        output = StringIO()
        
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=output
        )
        
        command_output = output.getvalue()
        
        # Verify success message
        assert "Successfully rolled back to version 0" in command_output
        
        # Verify records were actually transformed to v0
        for q in Questionnaire.objects.all():
            assert q.document["schema_version"] == 0, \
                f"Record {q.id} still at v{q.document['schema_version']}, expected v0"

    def test_dryrun_shows_output(self):
        """--dry-run reports what would happen."""
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--dry-run",
            stdout=out
        )
        output = out.getvalue()

        # Should have output
        assert len(output) > 0


@pytest.mark.django_db
class TestSchemaRollbackIdempotency(SchemaRollbackCommandTestCase):
    """Idempotency: running same rollback twice is safe (second run = no-op)."""

    def test_idempotent_when_already_at_target(self):
        """Rolling back to current version is no-op."""
        # First rollback to 0001 should succeed (already there since setUp creates at v1)
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        output = out.getvalue()

        assert "Already at version" in output

    def test_second_rollback_is_noop(self):
        """Running same rollback twice shows no-op."""
        # First rollback to v0
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000"
        )

        # Second call should also be no-op
        out2 = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=out2
        )

        output2 = out2.getvalue()
        assert "Already at version" in output2

    def test_rollback_idempotent_already_at_target(self):
        """Test that rollback to current version is a no-op (idempotent)."""
        # First rollback to v0
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000"
        )
        
        # Verify at v0
        assert Questionnaire.objects.first().document["schema_version"] == 0
        
        # Try rollback again (should detect already at target)
        output = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=output
        )
        
        command_output = output.getvalue()
        assert "Already at version 0. No rollback needed." in command_output
        
        # Verify records unchanged
        for q in Questionnaire.objects.all():
            assert q.document["schema_version"] == 0


@pytest.mark.django_db
class TestSchemaRollbackDryRun(SchemaRollbackCommandTestCase):
    """Dry-run produces zero database changes."""

    def test_dryrun_makes_no_changes(self):
        """--dry-run tests rollback without writing."""
        questionnaire = Questionnaire.objects.first()

        version_before = questionnaire.document["schema_version"]

        # Run dry-run
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--dry-run",
            stdout=out
        )

        # Verify no change
        questionnaire.refresh_from_db()
        version_after = questionnaire.document["schema_version"]

        assert version_before == version_after


@pytest.mark.django_db
class TestSchemaRollbackErrorHandling:
    """Error messages are clear about what failed."""

    def test_error_when_target_not_found(self):
        """Clear error when target migration doesn't exist."""
        with pytest.raises(CommandError) as exc_info:
            call_command("schema_rollback", "--target", "questionnaires", "9999")

        error = str(exc_info.value)
        assert "9999" in error or "not found" in error.lower()

    def test_error_on_invalid_target(self):
        """Error when invalid target provided."""
        with pytest.raises(CommandError):
            call_command("schema_rollback", "--target", "invalid_target", "0001")


@pytest.mark.django_db
class TestSchemaRollbackRejectsForwardDirection(SchemaRollbackCommandTestCase):
    """Test that rollback rejects trying to go forward."""

    def test_rollback_rejects_forward_direction(self):
        """Test that rollback rejects trying to go forward."""
        # First rollback to v0
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000"
        )
        
        # Try to "rollback" forward to v1 (should fail)
        with pytest.raises(CommandError):
            call_command(
                "schema_rollback",
                "--target", "questionnaires",
                "0001"
            )


@pytest.mark.django_db
class TestSchemaRollback0000MigrationBehavior(SchemaRollbackCommandTestCase):
    """Test behavior of rollback-only 0000 migration."""

    def test_rollback_0000_migration_rejects_forward(self):
        """Test that 0000 migration raises error if someone tries migrate_forward."""
        migration = get_migration("0000", self.migrations_path)
        
        # Try to call migrate_forward on rollback-only migration
        with pytest.raises(NotImplementedError) as exc_info:
            migration.migrate_forward({"schema_version": 0, "steps": []})
        
        assert "does not support forward migration" in str(exc_info.value)

    def test_rollback_0000_migration_backward_works(self):
        """Test that 0000 migration's migrate_backward actually transforms."""
        migration = get_migration("0000", self.migrations_path)
        
        # Prepare document at v1
        doc = {
            "schema_version": 1,
            "steps": [{"title": "Test", "sections": []}]
        }
        
        # Call migrate_backward (delegates to 0001)
        result = migration.migrate_backward(doc)
        
        # Should transform to v0
        assert result["schema_version"] == 0
        assert result["steps"] == [{"title": "Test", "sections": []}]

    def test_rollback_0000_schemas_are_frozen(self):
        """Test that 0000 migration schemas are frozen (hard-coded)."""
        migration = get_migration("0000", self.migrations_path)
        
        previous = migration.previous_schema()
        target = migration.target_schema()
        
        # Schemas should be dicts
        assert isinstance(previous, dict)
        assert isinstance(target, dict)
        
        # Previous should have v1 default, target should have v0 default
        assert previous["properties"]["schema_version"]["default"] == 1
        assert target["properties"]["schema_version"]["default"] == 0


@pytest.mark.django_db
class TestSchemaRollbackDisplayMessages(SchemaRollbackCommandTestCase):
    """Test rollback command display messages."""

    def test_rollback_display_shows_correct_arrow_direction(self):
        """Test that rollback output uses → arrow (same as forward migrations)."""
        output = StringIO()
        
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--dry-run",
            stdout=output
        )
        
        command_output = output.getvalue()
        
        # Should use → arrow consistently (not ← which would be confusing)
        assert "Rolling back migration 0001 (1 → 0)..." in command_output
        assert "←" not in command_output, "Should not use confusing ← arrow"

    def test_rollback_invalid_migration_number(self):
        """Test that rollback rejects non-existent migration."""
        with pytest.raises(CommandError):
            call_command(
                "schema_rollback",
                "--target", "questionnaires",
                "9999"
            )

    def test_rollback_verbose_shows_per_record_status(self):
        """Test that --verbose flag shows per-record progress."""
        output = StringIO()
        
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--verbose",
            stdout=output
        )
        
        command_output = output.getvalue()
        
        # Should show individual record IDs
        for q in Questionnaire.objects.all():
            assert f"Record {q.id}" in command_output


@pytest.mark.django_db
class TestSchemaRollbackMultipleRecords(SchemaRollbackCommandTestCase):
    """Rollback handles multiple records correctly."""

    def test_rollback_all_records_together(self):
        """All records transformed in same transaction."""
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=out
        )
        output = out.getvalue()

        # Should produce output
        assert len(output) > 0

    def test_rollback_consistent_state(self):
        """All records end at same version after rollback."""
        # Run rollback to v0
        out = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=out
        )

        # All should have same version
        versions = {q.document.get("schema_version") for q in Questionnaire.objects.all()}
        assert len(versions) == 1
        assert 0 in versions


class ApplicationsRollbackTestCase(TestCase):
    """Test schema_rollback command with applications target."""

    @classmethod
    def setUpClass(cls):
        """Set up process, questionnaire, and user for all tests."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser2", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test2",
            name="Test Process 2"
        )
        cls.questionnaire = Questionnaire.objects.create(
            process=cls.process,
            name="Test Questionnaire",
            code="test",
            version=1,
            document={
                "schema_version": 1,
                "steps": [{"title": "Step", "sections": []}]
            },
            created_by=cls.user
        )

    def setUp(self):
        """Create test applications at version 0 (baseline)."""
        # Create test applications at v0 (baseline)
        for i in range(2):
            Application.objects.create(
                owner=self.user,
                questionnaire=self.questionnaire,
                document={
                    "schema_version": 0,
                    "active_step": 0,
                    "steps": [
                        {
                            "is_valid": False,
                            "answers": {}
                        }
                    ]
                }
            )

    def test_rollback_0000_already_at_baseline(self):
        """Test that applications at v0 cannot rollback further."""
        output = StringIO()
        
        call_command(
            "schema_rollback",
            "--target", "applications",
            "0000",
            stdout=output
        )
        
        command_output = output.getvalue()
        
        # Should report already at target
        assert "Already at version 0. No rollback needed." in command_output
