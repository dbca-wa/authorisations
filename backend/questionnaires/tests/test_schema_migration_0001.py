"""Tests for schema migration 0001: Consolidate question config.

Tests forward migration (v0 → v1) and backward migration (v1 → v0)
for the question configuration consolidation refactoring.

Migration 0001 consolidates scattered question configuration fields into
a nested "config" object for improved schema clarity and API consistency.
"""

import importlib
import pytest

from schema_migration_framework.loader import get_migration
from schema_migration_framework.executor import get_migrations_package_path

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

# Ensure the schema_migrations package is importable
importlib.import_module("questionnaires.schema_migrations")

# Get the migrations package path for framework-based loading
_MIGRATIONS_PACKAGE_PATH = get_migrations_package_path("questionnaires.schema_migrations")


@pytest.fixture
def migration_0001():
    """Load migration 0001 via generic framework."""
    return get_migration("0001", _MIGRATIONS_PACKAGE_PATH)


class TestTargetSchema:
    """Test the target schema structure for version 1."""

    def test_target_schema_returns_dict(self, migration_0001):
        """Verify target_schema returns a valid schema dictionary."""
        schema = migration_0001.target_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema
        assert "$defs" in schema

    def test_target_schema_version_is_one(self, migration_0001):
        """Verify target schema has schema_version default of 1."""
        schema = migration_0001.target_schema()
        schema_version_prop = schema["properties"]["schema_version"]
        assert schema_version_prop["default"] == 1

    def test_target_schema_has_config_in_question(self, migration_0001):
        """Verify target schema defines config property in question."""
        schema = migration_0001.target_schema()
        question_def = schema["$defs"]["question"]
        assert "config" in question_def["properties"]
        config_prop = question_def["properties"]["config"]
        assert config_prop["type"] == "object"
        assert "properties" in config_prop
        assert set(config_prop["properties"].keys()) == {
            "select_options",
            "grid_columns",
            "grid_max_rows",
            "dependent_step",
            "file_max_attachments",
        }

    def test_target_schema_has_no_flat_config_fields(self, migration_0001):
        """Verify target schema does NOT have flat config fields at question level."""
        schema = migration_0001.target_schema()
        question_def = schema["$defs"]["question"]
        question_props = question_def["properties"].keys()
        
        flat_config_fields = {
            "select_options",
            "grid_columns",
            "grid_max_rows",
            "dependent_step",
            "file_max_attachments",
        }
        
        # All flat fields should be gone from question properties
        assert not flat_config_fields.intersection(question_props)


class TestPreviousSchema:
    """Test the previous schema structure for version 0."""

    def test_previous_schema_returns_dict(self, migration_0001):
        """Verify previous_schema returns a valid schema dictionary."""
        schema = migration_0001.previous_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema
        assert "$defs" in schema

    def test_previous_schema_version_is_zero(self, migration_0001):
        """Verify previous schema has schema_version default of 0."""
        schema = migration_0001.previous_schema()
        schema_version_prop = schema["properties"]["schema_version"]
        assert schema_version_prop["default"] == 0


class TestMigrateForward:
    """Test forward migration from schema v0 (flat) to v1 (nested)."""

    def test_migrate_forward_raises_on_wrong_version(self, migration_0001):
        """Verify migration raises TypeError if schema_version is not 0."""
        doc = {"schema_version": 1, "steps": []}
        with pytest.raises(TypeError, match="Expected schema_version 0"):
            migration_0001.migrate_forward(doc)

    def test_migrate_forward_simple_question_no_config(self, migration_0001):
        """Verify forward migration on question with no config fields."""
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Name",
                                    "type": "text",
                                    "is_required": True,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert question["label"] == "Name"
        assert question["type"] == "text"
        assert "config" not in question

    def test_migrate_forward_select_question(self, migration_0001):
        """Verify forward migration consolidates select_options into config."""
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Choose one",
                                    "type": "select",
                                    "is_required": False,
                                    "select_options": ["Option A", "Option B"],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "select_options" not in question
        assert "config" in question
        assert question["config"]["select_options"] == ["Option A", "Option B"]

    def test_migrate_forward_file_question(self, migration_0001):
        """Verify forward migration consolidates file_max_attachments into config."""
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Upload files",
                                    "type": "file",
                                    "is_required": True,
                                    "file_max_attachments": 5,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "file_max_attachments" not in question
        assert "config" in question
        assert question["config"]["file_max_attachments"] == 5

    def test_migrate_forward_grid_question(self, migration_0001):
        """Verify forward migration consolidates grid fields into config."""
        grid_columns = [
            {"label": "Col A", "type": "text"},
            {"label": "Col B", "type": "select", "select_options": ["X", "Y"]},
        ]
        
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Matrix",
                                    "type": "grid",
                                    "is_required": False,
                                    "grid_columns": grid_columns,
                                    "grid_max_rows": 10,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "grid_columns" not in question
        assert "grid_max_rows" not in question
        assert "config" in question
        assert question["config"]["grid_columns"] == grid_columns
        assert question["config"]["grid_max_rows"] == 10

    def test_migrate_forward_all_config_fields(self, migration_0001):
        """Verify forward migration with all config fields present."""
        grid_columns = [{"label": "Col", "type": "text"}]
        
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Complex Q",
                                    "type": "grid",
                                    "is_required": True,
                                    "select_options": ["A", "B"],
                                    "grid_columns": grid_columns,
                                    "grid_max_rows": 5,
                                    "dependent_step": 1,
                                    "file_max_attachments": 3,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        assert result["schema_version"] == 1
        question = result["steps"][0]["sections"][0]["questions"][0]
        
        # All flat fields should be gone
        assert "select_options" not in question
        assert "grid_columns" not in question
        assert "grid_max_rows" not in question
        assert "dependent_step" not in question
        assert "file_max_attachments" not in question
        
        # All should be in config
        assert question["config"]["select_options"] == ["A", "B"]
        assert question["config"]["grid_columns"] == grid_columns
        assert question["config"]["grid_max_rows"] == 5
        assert question["config"]["dependent_step"] == 1
        assert question["config"]["file_max_attachments"] == 3

    def test_migrate_forward_multiple_questions(self, migration_0001):
        """Verify forward migration handles multiple questions correctly."""
        doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Q1",
                                    "type": "text",
                                    "is_required": False,
                                },
                                {
                                    "label": "Q2",
                                    "type": "select",
                                    "is_required": False,
                                    "select_options": ["A", "B"],
                                },
                                {
                                    "label": "Q3",
                                    "type": "file",
                                    "is_required": False,
                                    "file_max_attachments": 2,
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_forward(doc)
        
        questions = result["steps"][0]["sections"][0]["questions"]
        
        # Q1: no config
        assert "config" not in questions[0]
        
        # Q2: config with select_options
        assert "config" in questions[1]
        assert questions[1]["config"]["select_options"] == ["A", "B"]
        
        # Q3: config with file_max_attachments
        assert "config" in questions[2]
        assert questions[2]["config"]["file_max_attachments"] == 2


class TestMigrateBackward:
    """Test backward migration from schema v1 (nested) to v0 (flat)."""

    def test_migrate_backward_raises_on_wrong_version(self, migration_0001):
        """Verify backward migration raises TypeError if schema_version is not 1."""
        doc = {"schema_version": 0, "steps": []}
        with pytest.raises(TypeError, match="Expected schema_version 1"):
            migration_0001.migrate_backward(doc)

    def test_migrate_backward_select_question(self, migration_0001):
        """Verify backward migration expands config.select_options to flat."""
        doc = {
            "schema_version": 1,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Choose one",
                                    "type": "select",
                                    "is_required": False,
                                    "config": {
                                        "select_options": ["Option A", "Option B"]
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_backward(doc)
        
        assert result["schema_version"] == 0
        question = result["steps"][0]["sections"][0]["questions"][0]
        assert "config" not in question
        assert question["select_options"] == ["Option A", "Option B"]

    def test_migrate_backward_all_config_fields(self, migration_0001):
        """Verify backward migration expands all config fields to flat."""
        grid_columns = [{"label": "Col", "type": "text"}]
        
        doc = {
            "schema_version": 1,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Complex Q",
                                    "type": "grid",
                                    "is_required": True,
                                    "config": {
                                        "select_options": ["A", "B"],
                                        "grid_columns": grid_columns,
                                        "grid_max_rows": 5,
                                        "dependent_step": 1,
                                        "file_max_attachments": 3,
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        
        result = migration_0001.migrate_backward(doc)
        
        assert result["schema_version"] == 0
        question = result["steps"][0]["sections"][0]["questions"][0]
        
        # All should be expanded to flat
        assert "config" not in question
        assert question["select_options"] == ["A", "B"]
        assert question["grid_columns"] == grid_columns
        assert question["grid_max_rows"] == 5
        assert question["dependent_step"] == 1
        assert question["file_max_attachments"] == 3


class TestRoundTripMigration:
    """Test forward and backward migration together (round-trip)."""

    def test_roundtrip_forward_then_backward(self, migration_0001):
        """Verify document is unchanged after forward then backward migration."""
        original_doc = {
            "schema_version": 0,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": [
                        {
                            "title": "Section 1",
                            "questions": [
                                {
                                    "label": "Q1",
                                    "type": "text",
                                    "is_required": False,
                                },
                                {
                                    "label": "Q2",
                                    "type": "select",
                                    "is_required": False,
                                    "select_options": ["A", "B"],
                                },
                                {
                                    "label": "Q3",
                                    "type": "file",
                                    "is_required": False,
                                    "file_max_attachments": 2,
                                },
                                {
                                    "label": "Q4",
                                    "type": "grid",
                                    "is_required": False,
                                    "grid_columns": [
                                        {"label": "Col A", "type": "text"}
                                    ],
                                    "grid_max_rows": 5,
                                    "dependent_step": 1,
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        
        # Forward: v0 → v1
        doc_v1 = migration_0001.migrate_forward(original_doc)
        assert doc_v1["schema_version"] == 1
        
        # Backward: v1 → v0
        doc_v0_restored = migration_0001.migrate_backward(doc_v1)
        assert doc_v0_restored["schema_version"] == 0
        
        # Should match original
        assert doc_v0_restored == original_doc
