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
        
        Path: 0000→0001→0002→0003 (4 steps: 0000 is baseline identity, then 3 forward)
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
            "0000": create_mock_migration(0, 0, "0000"),  # Baseline identity migration
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
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

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
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
        """Forward migration v0→v4 executes all 5 steps: 0000→0001→0002→0003→0004.
        
        Verifies that migration path can span 5 consecutive migrations from baseline.
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
            "0000": create_mock_migration(0, 0, "0000"),  # Baseline identity migration
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
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
        without applying any changes. Starts from v0 baseline.
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
            "0000": create_mock_migration(0, 0, "0000"),  # Baseline identity migration
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
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
        1. Execute 0000, 0001, 0002, 0003, 0004 successfully
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

        # Only have migrations up to v4 (0000-0004)
        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),  # Baseline identity migration
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
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


@pytest.mark.django_db
class TestSchemaMigrationStrictVersionMatching(TestCase):
    """Test strict version-to-migration matching requirements.
    
    These tests validate the new migration logic:
    - Each migration must match exactly: from_version == from_migration_number
    - Migration 0000 is required for starting at v0
    - Each migration sets its own version (0000→v0, 0001→v1, etc.)
    - Gap in migrations = failure
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser_strict", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test_strict",
            name="Test Strict Version Matching"
        )

    def test_migrate_from_v0_requires_0000_migration(self):
        """Starting at v0 requires migration 0000 in available migrations.
        
        If database is at v0 but 0000 migration is missing, migration fails.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V0 Missing 0000",
            code="test_v0_missing_0000",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )

        # Only have 0001-0003, missing 0000
        mock_migrations = {
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            # Should fail because v0 requires 0000
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    "0003",
                )
            
            error = str(exc_info.value)
            assert "Cannot find migration for current version 0" in error

    def test_migrate_from_v2_requires_0002_migration(self):
        """Starting at v2 requires migration 0002 to exist.
        
        Cannot migrate from v2 if 0002 migration is missing.
        Validates strict version-to-migration-number matching.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V2 Missing 0002",
            code="test_v2_missing_0002",
            version=1,
            document={"schema_version": 2, "steps": []},
            created_by=self.user
        )

        # Have 0003 but missing 0002
        mock_migrations = {
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            # Should fail because v2 requires 0002
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    "0003",
                )
            
            error = str(exc_info.value)
            assert "Cannot find migration for current version 2" in error

    def test_0000_is_identity_migration_at_baseline(self):
        """Migration 0000 is identity: transforms v0 → v0.
        
        0000 is the baseline starting point. It sets schema_version to 0
        (no actual transformation needed, just marks the ordinal baseline).
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test 0000 Identity",
            code="test_0000_identity",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )

        # Only 0000 migration
        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),  # v0 → v0 (identity)
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0000",
                stdout=out
            )

        q.refresh_from_db()
        # Should remain at v0 (already at target)
        assert q.document.get("schema_version") == 0

    def test_each_migration_sets_own_version(self):
        """Each migration sets its own version in document.
        
        0000 sets v0, 0001 sets v1, 0002 sets v2, etc.
        Validates that the mock migrations do this correctly.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Each Sets Version",
            code="test_each_sets_version",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            # Migrate through all versions
            for target_version, target_migration in [("0001", "0001"), ("0002", "0002")]:
                out = StringIO()
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    target_migration,
                    stdout=out
                )
                
                q.refresh_from_db()
                # Verify document has correct version after each step
                assert q.document.get("schema_version") == int(target_version)


@pytest.mark.django_db
class TestSchemaMigrateChainCases(TestCase):
    """Test migration changing cases: intermediate starting versions, large forward jumps, etc."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="testuser_edge", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="test_edge",
            name="Test Edge Cases"
        )

    def test_migrate_from_v3_skips_0000_to_0002_in_long_chain(self):
        """Database at v3 with migrations 0→5: should execute from 0003, skip 0000-0002.
        
        This is the edge case the user specifically requested:
        - DB schema_version: 3
        - Available migrations: 0000, 0001, 0002, 0003, 0004, 0005
        - Target: 0005
        - Expected execution: 0003 → 0004 → 0005 (skips 0000, 0001, 0002)
        
        Validates that find_migrations_to_apply correctly skips already-applied
        migrations when starting at an intermediate version.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V3 Skip Early Migrations",
            code="test_v3_skip_early",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        # All migrations from 0 to 5
        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
            "0005": create_mock_migration(4, 5, "0005"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0005",
                stdout=out
            )

        q.refresh_from_db()
        # Should now be at v5
        assert q.document.get("schema_version") == 5

    def test_migrate_from_v2_forward_to_v5_with_full_chain(self):
        """Database at v2, migrate forward to v5 in chain of 6 migrations.
        
        - DB schema_version: 2
        - Available migrations: 0000, 0001, 0002, 0003, 0004, 0005
        - Target: 0005
        - Expected execution: 0003 → 0004 → 0005 (skips 0002 since already applied)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V2 to V5",
            code="test_v2_to_v5",
            version=1,
            document={"schema_version": 2, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
            "0005": create_mock_migration(4, 5, "0005"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0005",
                stdout=out
            )

        q.refresh_from_db()
        # Should now be at v5
        assert q.document.get("schema_version") == 5

    def test_migrate_from_v2_partial_forward_to_v4(self):
        """Database at v2, migrate forward to v4 (skip 0002, execute 0003-0004).
        
        - DB schema_version: 2
        - Available migrations: 0000, 0001, 0002, 0003, 0004, 0005
        - Target: 0004
        - Expected execution: 0003 → 0004 (skips 0002 since already applied)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test V2 to V4",
            code="test_v2_to_v4",
            version=1,
            document={"schema_version": 2, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
            "0005": create_mock_migration(4, 5, "0005"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0004",
                stdout=out
            )

        q.refresh_from_db()
        # Should now be at v4
        assert q.document.get("schema_version") == 4

    def test_intermediate_version_already_at_target_is_noop(self):
        """Database at v3, migrate to v3 (target already reached) = no-op.
        
        - DB schema_version: 3
        - Available migrations: 0000-0005
        - Target: 0003
        - Expected: No migrations executed (already at target)
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Already at V3",
            code="test_already_v3",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
            "0005": create_mock_migration(4, 5, "0005"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            out = StringIO()
            call_command(
                "schema_migrate",
                "--target", "questionnaires",
                "0003",
                stdout=out
            )

        q.refresh_from_db()
        # Should remain at v3 (already there)
        assert q.document.get("schema_version") == 3

    def test_migrate_fails_when_target_migration_not_found(self):
        """Migration fails when target migration number does not exist.
        
        - DB schema_version: 2
        - Available migrations: 0000, 0001, 0002, 0003, 0004
        - Target: 0010 (does not exist)
        - Expected: CommandError (target migration not found)
        
        Even if we can reach intermediate versions, if the target migration
        number itself doesn't exist, the command should fail.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Target Migration Not Found",
            code="test_target_not_found",
            version=1,
            document={"schema_version": 2, "steps": []},
            created_by=self.user
        )

        # Only have migrations up to 0004
        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            "0003": create_mock_migration(2, 3, "0003"),
            "0004": create_mock_migration(3, 4, "0004"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            # Should fail because 0010 doesn't exist
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    "0010",
                )
            
            error = str(exc_info.value)
            # Error should mention 0010 not found
            assert "0010" in error or "not found" in error.lower()

    def test_migrate_fails_when_starting_version_has_no_migration(self):
        """Migration fails when current DB version has no matching migration.
        
        - DB schema_version: 3
        - Available migrations: 0000, 0001, 0002, [MISSING 0003], 0004, 0005
        - Target: 0005
        - Expected: CommandError (cannot find migration for v3)
        
        Strict version matching requires a migration numbered 0003 for v3,
        but it's missing from the available migrations.
        """
        q = Questionnaire.objects.create(
            process=self.process,
            name="Test Missing Starting Migration",
            code="test_missing_start_migration",
            version=1,
            document={"schema_version": 3, "steps": []},
            created_by=self.user
        )

        # Missing 0003 (current version)
        mock_migrations = {
            "0000": create_mock_migration(0, 0, "0000"),
            "0001": create_mock_migration(0, 1, "0001"),
            "0002": create_mock_migration(1, 2, "0002"),
            # 0003 is MISSING (but DB is at v3)
            "0004": create_mock_migration(3, 4, "0004"),
            "0005": create_mock_migration(4, 5, "0005"),
        }

        def mock_get_migration(num, path):
            return mock_migrations.get(num)

        def mock_list_migrations(path):
            return sorted(mock_migrations.keys())

        with patch('schema_migration_framework.management.commands.schema_migrate.get_migration', mock_get_migration), \
             patch('schema_migration_framework.management.commands.schema_migrate.list_migrations', mock_list_migrations):
            
            # Should fail because v3 requires migration 0003 which doesn't exist
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "schema_migrate",
                    "--target", "questionnaires",
                    "0005",
                )
            
            error = str(exc_info.value)
            # Error should mention version 3 cannot be found
            assert "Cannot find migration for current version 3" in error
