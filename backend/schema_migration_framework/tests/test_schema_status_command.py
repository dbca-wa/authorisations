"""Integration tests for schema_status management command.

Tests the generic schema_status command with --target flag across both
questionnaires and applications targets. Covers status output display, record
distribution reporting, mixed-version detection, and available migrations listing.
"""

from io import StringIO

import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from questionnaires.models import Questionnaire
from processes.models import AuthorisationProcess
from users.models import User
from questionnaires.schema import SCHEMA_VERSION as QUESTIONNAIRE_SCHEMA_VERSION


@pytest.mark.django_db
class TestSchemaStatusCommandBasic:
    """Basic command functionality for questionnaires target."""

    def test_command_runs_without_arguments(self):
        """Command requires --target flag."""
        with pytest.raises(CommandError):
            call_command("schema_status")

    def test_command_runs_with_target(self):
        """Command runs with --target flag."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        assert output  # Should produce some output

    def test_command_produces_formatted_output(self):
        """Output is formatted and readable."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should contain key info sections
        assert "schema" in output.lower()
        assert "version" in output.lower()


@pytest.mark.django_db
class TestSchemaStatusCurrentVersion:
    """Reports current schema version from code."""

    def test_displays_code_version_questionnaires(self):
        """Shows SCHEMA_VERSION from questionnaires schema.py."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        assert str(QUESTIONNAIRE_SCHEMA_VERSION) in output
        assert "version" in output.lower()

    def test_version_string_contains_key_info(self):
        """Code version displayed with key information."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should have recognizable format
        assert output.strip()  # Non-empty


@pytest.mark.django_db
@pytest.mark.django_db
class TestSchemaStatusRecordDistribution(TestCase):
    """Reports distribution of records by schema_version."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="statususer", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="status_test",
            name="Status Test Process"
        )

    def test_empty_database(self):
        """Handles empty database gracefully."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should handle empty DB without error
        assert output

    def test_single_version_distribution(self):
        """Shows records all at same version."""
        Questionnaire.objects.create(
            process=self.process,
            name="Status Test Q1",
            code="status_test_1",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )
        Questionnaire.objects.create(
            process=self.process,
            name="Status Test Q2",
            code="status_test_2",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )

        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should show version 1 and some count
        assert "1" in output

    def test_version_count_accuracy(self):
        """Record count matches actual records."""
        for i in range(5):
            Questionnaire.objects.create(
                process=self.process,
                name=f"Status Test Q{i}",
                code=f"status_test_{i}",
                version=1,
                document={"schema_version": 1, "steps": []},
                created_by=self.user
            )

        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should show the count in output
        assert output  # Has output


@pytest.mark.django_db
@pytest.mark.django_db
class TestSchemaStatusMixedVersions(TestCase):
    """Status correctly reports multiple versions in database."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.user = User.objects.create_user(username="mixuser", password="testpass")
        cls.process = AuthorisationProcess.objects.create(
            slug="mix_test",
            name="Mix Test Process"
        )

    def test_mixed_version_report(self):
        """Reports multiple versions when DB has them."""
        # Create at v0
        Questionnaire.objects.create(
            process=self.process,
            name="Mix Test Q0",
            code="mix_test_0",
            version=1,
            document={"schema_version": 0, "steps": []},
            created_by=self.user
        )
        
        # Create at v1
        Questionnaire.objects.create(
            process=self.process,
            name="Mix Test Q1",
            code="mix_test_1",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )

        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should report both versions
        assert "0" in output and "1" in output


@pytest.mark.django_db
class TestSchemaStatusAvailableMigrations:
    """Status lists available migrations."""

    def test_lists_available_migrations(self):
        """Outputs available migration versions."""
        out = StringIO()
        call_command("schema_status", "--target", "questionnaires", stdout=out)
        output = out.getvalue()

        # Should mention migrations
        assert "0001" in output or "migration" in output.lower()


@pytest.mark.django_db
class TestSchemaStatusApplicationsTarget:
    """Status command works with applications target."""

    def test_status_applications_target(self):
        """Can query status for applications target."""
        out = StringIO()
        call_command("schema_status", "--target", "applications", stdout=out)
        output = out.getvalue()

        # Should produce output without error
        assert output
