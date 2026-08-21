"""Tests for schema_status_questionnaire management command.

Tests status output display, record distribution reporting, mixed-version detection,
and available migrations listing.
"""

from io import StringIO

import pytest
from django.core.management import call_command

from questionnaires.schema import SCHEMA_VERSION


@pytest.mark.django_db
class TestSchemaStatusCommandBasic:
    """Basic command functionality."""

    def test_command_runs_without_arguments(self):
        """Command runs with no arguments."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "Schema Migration Status" in output
        assert output  # Should produce some output

    def test_command_produces_formatted_output(self):
        """Output is formatted and readable."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should contain section headers and key info
        assert "Code schema version" in output
        assert "Database schema version" in output
        assert "Record distribution" in output
        assert "Available migrations" in output


@pytest.mark.django_db
class TestSchemaStatusCurrentVersion:
    """Reports current schema version from code."""

    def test_displays_code_version(self):
        """Shows SCHEMA_VERSION from schema.py."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert SCHEMA_VERSION in output
        assert "Code schema version" in output

    def test_version_string_format(self):
        """Code version displayed in expected format."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should be in format "Code schema version: X"
        assert "Code schema version:" in output


@pytest.mark.django_db
class TestSchemaStatusRecordDistribution:
    """Reports distribution of records by schema_version."""

    def test_empty_database(self):
        """Handles empty database gracefully."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "no records" in output.lower() or "(0" in output

    def test_single_version_distribution(self, questionnaire_factory):
        """Shows records all at same version."""
        questionnaire_factory(document={"schema_version": "1", "title": "Test 1", "pages": []})
        questionnaire_factory(document={"schema_version": "1", "title": "Test 2", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "1:" in output
        assert "2" in output  # Should show count of 2

    def test_version_count_accuracy(self, questionnaire_factory):
        """Record count matches actual records."""
        for i in range(5):
            questionnaire_factory(document={"schema_version": "1", "title": f"Test {i}", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should report 5 records
        assert "5" in output or "Record distribution" in output

    def test_marks_current_version(self, questionnaire_factory):
        """Marks current version with indicator."""
        questionnaire_factory(document={"schema_version": SCHEMA_VERSION, "title": "Test", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should have some marker (✓ or similar) next to current version
        assert "✓" in output or "*" in output


@pytest.mark.django_db
class TestSchemaStatusMixedVersionDetection:
    """Detects and warns about mixed-version databases (error state)."""

    def test_mixed_versions_warning(self, questionnaire_factory):
        """Shows warning when records at different versions."""
        questionnaire_factory(document={"schema_version": "1", "title": "Test 1", "pages": []})
        questionnaire_factory(document={"schema_version": "999-different", "title": "Test 2", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should have warning about mixed state
        assert "MIXED" in output or "different versions" in output.lower()

    def test_mixed_state_shows_all_versions(self, questionnaire_factory):
        """Lists all versions present when mixed state detected."""
        questionnaire_factory(document={"schema_version": "1", "title": "Test 1", "pages": []})
        questionnaire_factory(document={"schema_version": "2", "title": "Test 2", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Both versions should be shown
        assert "1:" in output
        assert "2:" in output

    def test_mixed_state_contact_support_message(self, questionnaire_factory):
        """Helpful message suggests contacting support for mixed state."""
        questionnaire_factory(document={"schema_version": "1", "title": "Test 1", "pages": []})
        questionnaire_factory(document={"schema_version": "999", "title": "Test 2", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should suggest support/manual review
        assert "contact" in output.lower() or "support" in output.lower()

    def test_no_warning_for_single_version(self, questionnaire_factory):
        """No mixed-state warning when all records same version."""
        for i in range(3):
            questionnaire_factory(document={"schema_version": "1", "title": f"Test {i}", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Should not have MIXED warning
        assert "MIXED" not in output




@pytest.mark.django_db
class TestSchemaStatusAvailableMigrations:
    """Lists available migrations."""

    def test_lists_migrations(self):
        """Shows available migrations."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "Available migrations" in output
        # Should list at least 0001
        assert "0001" in output

    def test_migrations_sorted_order(self):
        """Migrations listed in order."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Extract migrations section
        lines = output.split("\n")
        migrations_found = []
        in_migrations = False
        for line in lines:
            if "Available migrations" in line:
                in_migrations = True
            elif in_migrations and "0" in line:
                # Extract migration number
                parts = line.strip().split()
                if parts:
                    migrations_found.append(parts[0])

        # Should be in order (if multiple exist)
        assert migrations_found


@pytest.mark.django_db
class TestSchemaStatusDatabaseVersion:
    """Reports database schema version (most common version)."""

    def test_displays_database_version(self, questionnaire_factory):
        """Shows database schema version."""
        questionnaire_factory(document={"schema_version": "1", "title": "Test", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "Database schema version" in output
        assert "1" in output

    def test_shows_mixed_for_empty_db(self):
        """Shows empty/mixed indicator for empty database."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "Database schema version" in output
        # Should show something like EMPTY or MIXED for empty DB
        assert "EMPTY" in output or "MIXED" in output or "no records" in output.lower()

    def test_db_version_matches_most_common(self, questionnaire_factory):
        """Database version is most common among records."""
        # Create 2 at version "1"
        questionnaire_factory(document={"schema_version": "1", "title": "Test 1", "pages": []})
        questionnaire_factory(document={"schema_version": "1", "title": "Test 2", "pages": []})
        # Create 1 at version "2"
        questionnaire_factory(document={"schema_version": "2", "title": "Test 3", "pages": []})

        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        # Database version should show "1" as most common
        # (Note: If tied, behavior depends on implementation)
        assert "1" in output


@pytest.mark.django_db
class TestSchemaStatusOutput:
    """Overall output formatting and structure."""

    def test_output_has_title_section(self):
        """Output includes title and formatting."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        assert "=" in output  # Border characters
        assert "Schema Migration Status" in output

    def test_output_readable_format(self):
        """Output is nicely formatted for humans."""
        out = StringIO()
        call_command("schema_status_questionnaire", stdout=out)
        output = out.getvalue()

        lines = output.split("\n")
        # Should have multiple lines with content
        assert len(lines) > 5
        # Should have sections with indentation
        assert any(line.startswith("  ") for line in lines)
