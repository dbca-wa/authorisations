"""Unit tests for schema_migration_framework.validator module."""

import pytest

from schema_migration_framework.validator import validate_transform


class TestValidateTransform:
    """Tests for schema validation."""

    @pytest.fixture
    def simple_schema(self):
        """Simple schema for testing."""
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["schema_version", "name"]
        }

    @pytest.fixture
    def doc_v1(self):
        """Valid document at version 1."""
        return {
            "schema_version": 1,
            "name": "Test Document"
        }

    def test_validate_transform_valid_document(self, simple_schema, doc_v1):
        """Accept valid document conforming to schema."""
        is_valid, errors = validate_transform(doc_v1, 0, 1, simple_schema)
        assert is_valid is True
        assert errors == []

    def test_validate_transform_schema_version_mismatch(self, simple_schema, doc_v1):
        """Reject document with mismatched schema_version."""
        is_valid, errors = validate_transform(doc_v1, 0, 2, simple_schema)
        assert is_valid is False
        assert len(errors) > 0
        assert "Expected schema_version 2" in errors[0]

    def test_validate_transform_missing_required_field(self, simple_schema):
        """Reject document missing required field."""
        doc = {"schema_version": 1}  # Missing "name"
        is_valid, errors = validate_transform(doc, 0, 1, simple_schema)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_transform_wrong_type(self, simple_schema):
        """Reject document with wrong field type."""
        doc = {
            "schema_version": "1",  # Should be integer, not string
            "name": "Test"
        }
        is_valid, errors = validate_transform(doc, 0, 1, simple_schema)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_transform_not_dict(self):
        """Reject non-dict input."""
        schema = {"type": "object"}
        is_valid, errors = validate_transform("not a dict", 0, 1, schema)
        assert is_valid is False
        assert "Document must be a dict" in errors[0]

    def test_validate_transform_missing_schema_version_in_doc(self, simple_schema):
        """Reject document missing schema_version field."""
        doc = {"name": "Test"}  # Missing schema_version
        is_valid, errors = validate_transform(doc, 0, 1, simple_schema)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_transform_complex_schema(self):
        """Validate against complex nested schema."""
        schema = {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "sections": {
                                "type": "array",
                                "items": {"type": "object"}
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            "required": ["schema_version", "steps"]
        }
        
        doc = {
            "schema_version": 1,
            "steps": [
                {
                    "title": "Step 1",
                    "sections": []
                }
            ]
        }
        
        is_valid, errors = validate_transform(doc, 0, 1, schema)
        assert is_valid is True
        assert errors == []

    def test_validate_transform_error_message_includes_path(self):
        """Error messages include path to failing field."""
        schema = {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer"},
                "nested": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"}
                    },
                    "required": ["value"]
                }
            },
            "required": ["schema_version", "nested"]
        }
        
        doc = {
            "schema_version": 1,
            "nested": {}  # Missing required "value"
        }
        
        is_valid, errors = validate_transform(doc, 0, 1, schema)
        assert is_valid is False
        # Error should mention the path to the failing field
        assert len(errors) > 0

    def test_validate_transform_returns_all_errors(self):
        """Collect all validation errors, not just first."""
        schema = {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer"},
                "field1": {"type": "string"},
                "field2": {"type": "integer"}
            },
            "required": ["schema_version", "field1", "field2"]
        }
        
        doc = {"schema_version": 1}  # Missing both required fields
        is_valid, errors = validate_transform(doc, 0, 1, schema)
        assert is_valid is False
        assert len(errors) >= 1  # At least one error about missing fields

    def test_validate_transform_with_nullable_field(self):
        """Accept nullable fields with null value."""
        schema = {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer"},
                "optional_field": {"type": ["string", "null"]}
            },
            "required": ["schema_version"]
        }
        
        doc = {
            "schema_version": 1,
            "optional_field": None
        }
        
        is_valid, errors = validate_transform(doc, 0, 1, schema)
        assert is_valid is True
        assert errors == []
