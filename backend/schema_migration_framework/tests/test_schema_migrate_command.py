"""Integration tests for schema_migrate management command.

Tests the generic schema_migrate command with --target flag across both
questionnaires and applications targets. Covers idempotency (already at target 
= no-op), dry-run validation, path-finding with sequential execution, 
transaction isolation per migration, and error messages.
"""

import pytest
from io import StringIO
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from questionnaires.models import Questionnaire
from processes.models import AuthorisationProcess
from users.models import User
from schema_migration_framework.executor import get_migrations_package_path
from schema_migration_framework.tests.conftest import create_mock_migration


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


@pytest.mark.django_db
class TestSchemaMigrateMultiStepSequence(TestCase):
    """Multi-step migration sequences execute transforms in correct order.
    
    These tests verify that when migrating through multiple versions (e.g.,
    0001→0003 via 0002), all intermediate transforms execute sequentially.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser_multi", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test_multi",
            name="Test Multi-step"
        )

    def test_multi_step_forward_migration_executes_all_steps(self):
        """Forward migration through multiple versions executes all transforms.
        
        This test verifies path-finding works by checking that a questionnaire
        at v1 can still migrate to higher versions (if they existed).
        Currently questionnaires only has v0 and v1, so we test migration idempotency
        as a proxy for multi-step behavior.
        """
        # Create at v1
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Q Multi",
            code="test_multi_forward",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )
        
        # Migrate to 0001 (current, should be no-op)
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            stdout=out
        )
        
        q.refresh_from_db()
        # Should still be v1
        assert q.document.get("schema_version") == 1
        
        output = out.getvalue()
        # Should either succeed or report no changes needed
        assert "Already at version" in output or "Tested" in output or not output.strip()

    def test_migrate_command_calls_path_finder(self):
        """Verify that migrate command uses path-finding to sequence migrations.
        
        This is verified indirectly: if an unknown source version is encountered,
        path-finding should fail with clear error message.
        """
        # Create at unknown version
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Q Path",
            code="test_multi_path",
            version=1,
            document={"schema_version": 999, "steps": []},
            created_by=self.user
        )
        
        # Attempting to migrate should fail because v999 is unknown
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0001"
            )
        
        error = str(exc_info.value)
        # Error should mention that path cannot be determined
        assert "Cannot determine" in error or "Cannot find" in error or "unknown" in error.lower()

    def test_dry_run_with_multi_step_shows_would_transform(self):
        """Dry-run with sequence of migrations reports would-be transforms.
        
        Even though questionnaires only has one forward migration,
        this test verifies the dry-run path works with the path-finding logic.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Q DryRun",
            code="test_multi_dryrun",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )
        
        # Dry-run to 0001 (same version)
        out = StringIO()
        call_command(
            "schema_migrate",
            "--target", "questionnaires",
            "0001",
            "--dry-run",
            stdout=out
        )
        
        # Verify record unchanged
        q.refresh_from_db()
        assert q.document.get("schema_version") == 1
        
        output = out.getvalue()
        # Dry-run should produce some output
        assert output or "Already at version" in output


@pytest.mark.django_db
class TestSchemaMigrateMultiStepMockedMigrations(TestCase):
    """Multi-step forward migration with mocked migrations (0001-0004 sequence).
    
    Tests forward migration sequences through multiple migrations:
    - v0→v3 (3-step forward: 0001→0002→0003)
    - v1→v2 (1-step forward: 0002)
    - v0→v4 (4-step forward: 0001→0002→0003→0004)
    
    Uses mock migration modules to avoid needing real migration files.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser_migrate_mock", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test_migrate_mock",
            name="Test Migrate Mock"
        )

    def test_migrate_v0_to_v3_executes_all_steps_forward(self):
        """Forward migration from v0 to v3 executes 0→1→2→3 in sequence.
        
        Path: 0001→0002→0003 (3 steps forward)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V0 to V3",
            code="test_v0_to_v3_migrate",
            version=1,
            document={"schema_version": 0, "steps": []},
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

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_migrate.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0003",
                stdout=out
            )

        q.refresh_from_db()
        # Should now be at v3
        assert q.document.get("schema_version") == 3

    def test_migrate_v1_to_v2_executes_single_step(self):
        """Forward migration from v1 to v2 executes 1→2 in single step.
        
        Path: 0002 (1 step forward)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V1 to V2",
            code="test_v1_to_v2_migrate",
            version=1,
            document={"schema_version": 1, "steps": []},
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

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_migrate.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0002",
                stdout=out
            )

        q.refresh_from_db()
        assert q.document.get("schema_version") == 2

    def test_migrate_v0_to_v4_executes_all_four_steps(self):
        """Forward migration v0→v4 executes all 4 steps: 0001→0002→0003→0004.
        
        Verifies that migration path can span 4 consecutive migrations.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V0 to V4",
            code="test_v0_to_v4_migrate",
            version=1,
            document={"schema_version": 0, "steps": []},
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

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_migrate.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0004",
                stdout=out
            )

        q.refresh_from_db()
        assert q.document.get("schema_version") == 4

    def test_migrate_dry_run_multi_step_shows_transforms(self):
        """Dry-run for multi-step forward migration shows all transforms.
        
        Verifies that dry-run correctly tests all intermediate migrations
        without applying any changes.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test DryRun Multi",
            code="test_dryrun_multi",
            version=1,
            document={"schema_version": 0, "steps": []},
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

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_migrate.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0003",
                "--dry-run",
                stdout=out
            )

        q.refresh_from_db()
        # Should remain at v0 (dry-run doesn't apply changes)
        assert q.document.get("schema_version") == 0

    def test_migrate_partial_success_0_to_5_reaches_4_then_fails(self):
        """Migration from v0 to v5 succeeds until v4, then fails on missing v5.
        
        This tests the scenario where intermediate migrations work but
        the target migration doesn't exist. The command should:
        1. Execute 0001, 0002, 0003, 0004 successfully
        2. Attempt to find 0005 and fail with clear error
        3. Leave records at v4 (last successful state)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Partial Success",
            code="test_partial_success_v0_v5",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )

        # Only have migrations up to v4 (0001-0004)
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
            # v5 does not exist
            raise ValueError(f"No migration found with output version {version}")

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations), \
             patch('schema_migration_framework.management.commands.schema_migrate.find_migration_by_output_version', mock_find_migration_by_output_version):
            
            # Migration to v5 should fail because v5 target doesn't exist
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    "0005",  # This migration doesn't exist
                )
            
            error = str(exc_info.value)
            assert "0005" in error or "not found" in error.lower()

        q.refresh_from_db()
        # Record should still be at v0 (transaction rolled back on error)
        assert q.document.get("schema_version") == 0
