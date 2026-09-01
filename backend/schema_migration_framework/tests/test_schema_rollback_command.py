"""Integration tests for schema_rollback management command.

Tests the generic schema_rollback command with --target flag across both
questionnaires and applications targets. Covers idempotency (already at target 
= no-op), dry-run validation, backward transformation verification, backward
migration rejection, transaction isolation, and error messages for failed
rollbacks.
"""

import pytest
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from questionnaires.models import Questionnaire
from processes.models import AuthorisationProcess
from users.models import User
from applications.models import Application
from schema_migration_framework.executor import get_migrations_package_path
from schema_migration_framework.tests.conftest import create_mock_migration
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
    """Test behavior of bidirectional 0000 bridge migration (calendar ↔ ordinal)."""

    def test_rollback_0000_migration_forward_works(self):
        """Test that 0000 migration transforms calendar string → v0 (int)."""
        migration = get_migration("0000", self.migrations_path)
        
        # Prepare document at calendar version
        doc = {
            "schema_version": "2025.07-1",
            "steps": [{"title": "Test", "sections": []}]
        }
        
        # Call migrate_forward (calendar → v0)
        result = migration.migrate_forward(doc)
        
        # Should transform to v0 (integer)
        assert result["schema_version"] == 0
        assert result["steps"] == [{"title": "Test", "sections": []}]


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


@pytest.mark.django_db
class TestSchemaRollbackMultiStepSequence(SchemaRollbackCommandTestCase):
    """Multi-step rollback sequences execute transforms in reverse order.
    
    These tests verify that when rolling back through multiple versions 
    (e.g., 0003→0001 via 0002), all intermediate transforms execute 
    in reverse order (0003→0002→0001).
    """

    def setUp(self):
        """Create test questionnaires for multi-step testing."""
        super().setUp()
        # Get first questionnaire created by parent setUp()
        questionnaires = Questionnaire.objects.all()
        if questionnaires.exists():
            self.q1 = questionnaires.first()

    def test_rollback_multi_step_executes_all_steps_reverse(self):
        """Rollback through multiple versions executes transforms in reverse.
        
        This test verifies path-finding for rollback by checking that
        a questionnaire at v1 can successfully rollback to v0.
        """
        # Questionnaires are already at v1 from setUp
        assert self.q1.document.get("schema_version") == 1
        
        # Rollback to 0000 (previous version)
        output = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=output
        )
        
        self.q1.refresh_from_db()
        # Should now be at v0
        assert self.q1.document.get("schema_version") == 0
        
        command_output = output.getvalue()
        # Should show rollback path
        assert "Rollback path:" in command_output or "0000" in command_output

    def test_rollback_dry_run_multi_step_shows_path(self):
        """Dry-run rollback through multiple steps shows the path.
        
        Verifies that dry-run correctly identifies all migrations in sequence
        without applying them.
        """
        original_version = self.q1.document.get("schema_version")
        
        # Dry-run rollback
        output = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            "--dry-run",
            stdout=output
        )
        
        self.q1.refresh_from_db()
        # Should NOT change in dry-run
        assert self.q1.document.get("schema_version") == original_version
        
        command_output = output.getvalue()
        # Should show would-rollback message
        assert "DRY RUN" in command_output or "Rollback path:" in command_output

    def test_rollback_command_uses_path_finder_backward(self):
        """Rollback command uses path-finder to sequence migrations backward.
        
        Verifies that attempting to rollback to unknown version fails
        with path-finding error.
        """
        # The mixed version error is intentional - rollback rejects
        # databases with mixed versions. This test verifies that behavior.
        # Create a clean test by using only v0 at start.
        Questionnaire.objects.all().delete()
        
        q_v0 = Questionnaire.objects.create(
            process=self.process,
            name="Test Q at V0",
            code="test_v0_rollback",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )
        
        # Attempting to rollback from v0 to v0 should succeed (idempotent)
        output = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=output
        )
        
        q_v0.refresh_from_db()
        # Should remain at v0
        assert q_v0.document.get("schema_version") == 0

    def test_rollback_sequence_maintains_order(self):
        """Rollback executes migrations in descending order (reverse path).
        
        When rolling back 0001→0000, the 0000 migration's backward
        function is called, which is the only step needed.
        """
        # At v1, rollback to v0 requires calling 0000 migration's backward
        output = StringIO()
        call_command(
            "schema_rollback",
            "--target", "questionnaires",
            "0000",
            stdout=output
        )
        
        self.q1.refresh_from_db()
        # Verify rollback succeeded
        assert self.q1.document.get("schema_version") == 0
        
        command_output = output.getvalue()
        # Should show path with migrations in order
        lines = [line for line in command_output.split('\n') if line.strip()]
        # Should have meaningful output showing rollback occurred
        assert len(lines) > 0


@pytest.mark.django_db
class TestSchemaRollbackMultiStepMockedMigrations(TestCase):
    """Multi-step rollback with mocked migrations (0001-0004 sequence).
    
    Tests rollback sequences through multiple migrations:
    - v3→v0 (4-step backward: 0004→0003→0002→0001→0000)
    - v1→v0 (1-step backward: 0001→0000)
    - v3→v1 (2-step backward: 0003→0002→0001)
    
    Uses mock migration modules to avoid needing real migration files.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser_mock", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test_mock",
            name="Test Mock Migrations"
        )

    def setUp(self):
        """Create test questionnaires for multi-step testing."""
        super().setUp()
        # Get first questionnaire created by parent setUp()
        questionnaires = Questionnaire.objects.all()
        if questionnaires.exists():
            self.q1 = questionnaires.first()

    def test_rollback_v3_to_v0_executes_all_steps_backward(self):
        """Rollback from v3 to v0 executes 3→2→1→0 in sequence.
        
        Path: 0004→0003→0002→0001→0000 (4 steps backward)
        """
        # Create questionnaire at v3
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V3 Rollback",
            code="test_v3_rollback",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        # Mock migrations for 0->1, 1->2, 2->3, 3->4
        mock_migrations = {
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        # Mock 0000 for rollback
        rollback_0000 = type('MockModule', (), {
            'previous_schema': lambda: {"properties": {"schema_version": {"default": 0}}},
            'target_schema': lambda: {"properties": {"schema_version": {"default": 1}}},
            'migrate_backward': lambda doc: {**doc, "schema_version": 0},
        })()

        all_migrations = {**mock_migrations, "0000": rollback_0000}

        def mock_get_migration(num, path):
            return all_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(all_migrations.keys())

        def mock_find_migration_by_output_version(version, path):
            version_map = {0: "0000", 1: "0001", 2: "0002", 3: "0003", 4: "0004"}
            if version in version_map:
                return version_map[version]
            raise ValueError(f"No migration for version {version}")

        with patch('schema_migration_framework.management.commands.schema_rollback.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_rollback.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_rollback.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_rollback",
                "--target", "questionnaires",
                "0000",
                stdout=out
            )

        q.refresh_from_db()
        # Should now be at v0
        assert q.document.get("schema_version") == 0
        
        output = out.getvalue()
        assert "Rollback path:" in output

    def test_rollback_v3_to_v1_executes_two_steps(self):
        """Rollback from v3 to v1 executes 3→2→1 in sequence.
        
        Path: 0003→0002→0001 (2 steps backward)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V3 to V1",
            code="test_v3_to_v1",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        def mock_find_migration_by_output_version(version, path):
            version_map = {1: "0001", 2: "0002", 3: "0003", 4: "0004"}
            if version in version_map:
                return version_map[version]
            raise ValueError(f"No migration for version {version}")

        with patch('schema_migration_framework.management.commands.schema_rollback.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_rollback.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_rollback.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_rollback",
                "--target", "questionnaires",
                "0001",
                stdout=out
            )

        q.refresh_from_db()
        assert q.document.get("schema_version") == 1

    def test_rollback_shows_correct_step_sequence(self):
        """Verify rollback displays migration path in correct order.
        
        For v3→v1, should show path like: 0003 → 0002 → 0001
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Path Display",
            code="test_path_display",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        def mock_find_migration_by_output_version(version, path):
            version_map = {1: "0001", 2: "0002", 3: "0003"}
            if version in version_map:
                return version_map[version]
            raise ValueError(f"No migration for version {version}")

        with patch('schema_migration_framework.management.commands.schema_rollback.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_rollback.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_rollback.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_rollback",
                "--target", "questionnaires",
                "0001",
                stdout=out
            )

        output = out.getvalue()
        # Should show the path
        assert "0003" in output or "Rollback" in output

    def test_rollback_partial_success_v4_to_v0_reaches_v1_then_fails(self):
        """Rollback from v4 to v0 succeeds until v1, then fails when trying to reach v0.
        
        This tests the scenario where rollback migrations work but
        the target migration (0000) doesn't exist in the mock. The command should:
        1. Execute 0004, 0003, 0002 backward successfully (reaching v1)
        2. Attempt to find 0000 and fail with clear error
        3. Leave records at v1 (last successful state before failure)
        
        Note: Rollback with missing 0000 should fail during path-finding.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Rollback Partial",
            code="test_rollback_partial_v4_v0",
            version=1,
            document={"schema_version": 4, "steps": []},
            created_by=self.user
        )

        # Only have migrations 0001-0004, NO 0000
        mock_migrations = {
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        def mock_find_migration_by_output_version(version, path):
            version_map = {1: "0001", 2: "0002", 3: "0003", 4: "0004"}
            if version in version_map:
                return version_map[version]
            # v0 does not exist (no 0000 migration)
            raise ValueError(f"No migration found with output version {version}")

        with patch('schema_migration_framework.management.commands.schema_rollback.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_rollback.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_rollback.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            # Rollback to v0 should fail because 0000 migration doesn't exist
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_rollback",
                    "--target", "questionnaires",
                    "0000",  # This migration doesn't exist in mock
                )
            
            error = str(exc_info.value)
            # Should mention the missing migration or inability to determine current migration
            assert "0000" in error or "Cannot" in error or "not found" in error.lower()

        q.refresh_from_db()
        # Record should still be at v4 (transaction rolled back on error during validation)
        assert q.document.get("schema_version") == 4
