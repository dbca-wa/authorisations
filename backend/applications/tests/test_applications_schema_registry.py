"""Test applications target registration in schema migration registry."""

import pytest
from schema_migration_framework.registry import get_target, list_target_keys, load_targets


@pytest.mark.unit
class TestApplicationsSchemaRegistry:
    """Verify applications is registered in SCHEMA_MIGRATION_TARGETS."""
    
    def test_applications_target_registered(self):
        """Applications target should be in registry."""
        targets = load_targets()
        target = get_target("applications", targets)
        
        assert target is not None
        assert target["key"] == "applications"
    
    def test_applications_target_has_correct_model(self):
        """Applications target should reference applications.Application model."""
        targets = load_targets()
        target = get_target("applications", targets)
        
        assert target["model"] == "applications.Application"
    
    def test_applications_target_configuration_complete(self):
        """Applications target should have all required configuration fields."""
        targets = load_targets()
        target = get_target("applications", targets)
        
        required_fields = [
            "key",
            "model",
            "json_field",
            "schema_provider",
            "migrations_package",
            "version_path",
        ]
        
        for field in required_fields:
            assert field in target, f"Missing required field: {field}"
    
    def test_applications_target_configuration_values(self):
        """Verify applications target configuration values."""
        targets = load_targets()
        target = get_target("applications", targets)
        
        assert target["json_field"] == "document"
        assert target["version_path"] == "schema_version"
        assert "applications.schema_migrations" in target["migrations_package"]
    
    def test_both_questionnaires_and_applications_registered(self):
        """Both questionnaires and applications should be registered."""
        targets = load_targets()
        keys = list_target_keys(targets)
        
        assert "questionnaires" in keys
        assert "applications" in keys
    
    def test_no_duplicate_target_keys(self):
        """Target keys should be unique in registry."""
        targets = load_targets()
        keys = [target["key"] for target in targets]
        
        assert len(keys) == len(set(keys)), "Duplicate target keys found"
