"""Unit tests for schema_migration_framework.registry module."""

import pytest
from django.test import override_settings

from schema_migration_framework.registry import (
    RegistryError,
    get_target,
    list_target_keys,
    load_targets,
    validate_no_duplicate_keys,
)


@pytest.fixture
def valid_target():
    """Valid target configuration fixture."""
    return {
        "key": "questionnaires",
        "model": "questionnaires.Questionnaire",
        "json_field": "document",
        "schema_provider": "questionnaires.schema.SCHEMA_VERSION",
        "migrations_package": "questionnaires.schema_migrations",
        "version_path": "schema_version",
    }


@pytest.fixture
def valid_targets(valid_target):
    """Valid targets list fixture."""
    return [
        valid_target,
        {
            "key": "applications",
            "model": "applications.Application",
            "json_field": "document",
            "schema_provider": "applications.schema.SCHEMA_VERSION",
            "migrations_package": "applications.schema_migrations",
            "version_path": "schema_version",
        },
    ]


class TestLoadTargets:
    """Tests for load_targets() function."""

    def test_load_targets_missing_setting_raises_error(self):
        """Raise error if SCHEMA_MIGRATION_TARGETS setting not defined."""
        with pytest.raises(
            RegistryError, match="SCHEMA_MIGRATION_TARGETS setting not found"
        ):
            load_targets()

    def test_load_targets_not_a_list_raises_error(self):
        """Raise error if SCHEMA_MIGRATION_TARGETS is not a list."""
        with override_settings(SCHEMA_MIGRATION_TARGETS="not a list"):
            with pytest.raises(RegistryError, match="must be a list"):
                load_targets()

    def test_load_targets_empty_list_raises_error(self):
        """Raise error if SCHEMA_MIGRATION_TARGETS is empty."""
        with override_settings(SCHEMA_MIGRATION_TARGETS=[]):
            with pytest.raises(RegistryError, match="is empty"):
                load_targets()

    def test_load_targets_valid_single_target(self, valid_target):
        """Load valid single target successfully."""
        with override_settings(SCHEMA_MIGRATION_TARGETS=[valid_target]):
            targets = load_targets()
            assert len(targets) == 1
            assert targets[0]["key"] == "questionnaires"

    def test_load_targets_valid_multiple_targets(self, valid_targets):
        """Load valid multiple targets successfully."""
        with override_settings(SCHEMA_MIGRATION_TARGETS=valid_targets):
            targets = load_targets()
            assert len(targets) == 2
            assert targets[0]["key"] == "questionnaires"
            assert targets[1]["key"] == "applications"

    def test_load_targets_validates_each_target(self, valid_target):
        """Validate each target in the list."""
        invalid_target = valid_target.copy()
        invalid_target.pop("key")  # Remove required field
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[invalid_target]):
            with pytest.raises(RegistryError, match="Missing required field"):
                load_targets()

    def test_load_targets_detects_duplicate_keys(self, valid_target):
        """Detect duplicate keys across targets."""
        target1 = valid_target.copy()
        target2 = valid_target.copy()
        target2["model"] = "different.Model"
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target1, target2]):
            with pytest.raises(RegistryError, match="Duplicate target key"):
                load_targets()


class TestValidateTarget:
    """Tests for target validation logic."""

    def test_target_not_dict_raises_error(self):
        """Raise error if target is not a dict."""
        with override_settings(SCHEMA_MIGRATION_TARGETS=["not a dict"]):
            with pytest.raises(RegistryError, match="Expected dict"):
                load_targets()

    def test_target_missing_key_field_raises_error(self, valid_target):
        """Raise error if 'key' field missing."""
        target = valid_target.copy()
        target.pop("key")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'key'"):
                load_targets()

    def test_target_missing_model_field_raises_error(self, valid_target):
        """Raise error if 'model' field missing."""
        target = valid_target.copy()
        target.pop("model")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'model'"):
                load_targets()

    def test_target_missing_json_field_raises_error(self, valid_target):
        """Raise error if 'json_field' field missing."""
        target = valid_target.copy()
        target.pop("json_field")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'json_field'"):
                load_targets()

    def test_target_missing_schema_provider_raises_error(self, valid_target):
        """Raise error if 'schema_provider' field missing."""
        target = valid_target.copy()
        target.pop("schema_provider")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'schema_provider'"):
                load_targets()

    def test_target_missing_migrations_package_raises_error(self, valid_target):
        """Raise error if 'migrations_package' field missing."""
        target = valid_target.copy()
        target.pop("migrations_package")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'migrations_package'"):
                load_targets()

    def test_target_missing_version_path_raises_error(self, valid_target):
        """Raise error if 'version_path' field missing."""
        target = valid_target.copy()
        target.pop("version_path")
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="Missing required field 'version_path'"):
                load_targets()

    def test_target_key_wrong_type_raises_error(self, valid_target):
        """Raise error if 'key' is not string."""
        target = valid_target.copy()
        target["key"] = 123
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="'key' must be string"):
                load_targets()

    def test_target_model_wrong_type_raises_error(self, valid_target):
        """Raise error if 'model' is not string."""
        target = valid_target.copy()
        target["model"] = 123
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="'model' must be string"):
                load_targets()

    def test_target_model_missing_dot_raises_error(self, valid_target):
        """Raise error if 'model' format is invalid (no dot)."""
        target = valid_target.copy()
        target["model"] = "InvalidModel"
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="must be in format 'app_label.ModelName'"):
                load_targets()

    def test_target_schema_provider_missing_dot_raises_error(self, valid_target):
        """Raise error if 'schema_provider' format is invalid (no dot)."""
        target = valid_target.copy()
        target["schema_provider"] = "INVALID"
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="must be dotted import path"):
                load_targets()

    def test_target_migrations_package_missing_dot_raises_error(self, valid_target):
        """Raise error if 'migrations_package' format is invalid (no dot)."""
        target = valid_target.copy()
        target["migrations_package"] = "schema_migrations"
        
        with override_settings(SCHEMA_MIGRATION_TARGETS=[target]):
            with pytest.raises(RegistryError, match="must be dotted import path"):
                load_targets()


class TestGetTarget:
    """Tests for get_target() lookup function."""

    def test_get_target_finds_existing_target(self, valid_targets):
        """Find target by key when it exists."""
        target = get_target("questionnaires", valid_targets)
        assert target is not None
        assert target["key"] == "questionnaires"
        assert target["model"] == "questionnaires.Questionnaire"

    def test_get_target_returns_none_when_not_found(self, valid_targets):
        """Return None when target key not found."""
        target = get_target("nonexistent", valid_targets)
        assert target is None

    def test_get_target_returns_correct_target_among_many(self, valid_targets):
        """Return correct target when multiple targets exist."""
        target = get_target("applications", valid_targets)
        assert target is not None
        assert target["model"] == "applications.Application"


class TestListTargetKeys:
    """Tests for list_target_keys() function."""

    def test_list_target_keys_returns_all_keys(self, valid_targets):
        """Return all target keys in order."""
        keys = list_target_keys(valid_targets)
        assert keys == ["questionnaires", "applications"]

    def test_list_target_keys_empty_list(self):
        """Return empty list when no targets."""
        keys = list_target_keys([])
        assert keys == []

    def test_list_target_keys_single_target(self, valid_target):
        """Return single key for single target."""
        keys = list_target_keys([valid_target])
        assert keys == ["questionnaires"]


class TestValidateNoDuplicateKeys:
    """Tests for validate_no_duplicate_keys() function."""

    def test_validate_no_duplicates_passes_for_unique_keys(self, valid_targets):
        """Pass validation when all keys are unique."""
        validate_no_duplicate_keys(valid_targets)  # Should not raise

    def test_validate_no_duplicates_raises_for_duplicate_keys(self, valid_target):
        """Raise error when duplicate keys found."""
        target1 = valid_target.copy()
        target2 = valid_target.copy()
        target2["model"] = "different.Model"
        
        with pytest.raises(RegistryError, match="Duplicate target key"):
            validate_no_duplicate_keys([target1, target2])

    def test_validate_no_duplicates_empty_list(self):
        """Pass validation for empty targets list."""
        validate_no_duplicate_keys([])  # Should not raise

    def test_validate_no_duplicates_single_target(self, valid_target):
        """Pass validation for single target."""
        validate_no_duplicate_keys([valid_target])  # Should not raise
