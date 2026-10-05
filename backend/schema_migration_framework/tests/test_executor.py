"""Unit tests for schema_migration_framework.executor module."""

from copy import deepcopy

import pytest

from schema_migration_framework.executor import (
    apply_transforms,
    get_db_schema_version,
    validate_all_transforms,
)


class MockRecord:
    """Mock record with document and save capability."""

    def __init__(self, doc: dict):
        """Initialize mock record with document."""
        self.document = doc
        self.saved = False
        self.save_kwargs = None

    def save(self, **kwargs):
        """Mark as saved."""
        self.saved = True
        self.save_kwargs = kwargs


class TestGetDbSchemaVersion:
    """Tests for getting current database schema version."""

    def test_get_db_schema_version_all_same_version(self):
        """Return version when all records at same version."""
        records = [
            MockRecord({"schema_version": 1}),
            MockRecord({"schema_version": 1}),
            MockRecord({"schema_version": 1}),
        ]
        version_accessor = lambda r: r.document.get("schema_version")
        
        version = get_db_schema_version(records, version_accessor)
        assert version == 1

    def test_get_db_schema_version_empty_records(self):
        """Return None for empty records list."""
        records = []
        version_accessor = lambda r: r.document.get("schema_version")
        
        version = get_db_schema_version(records, version_accessor)
        assert version is None

    def test_get_db_schema_version_mixed_versions_raises_error(self):
        """Raise RuntimeError if records at different versions."""
        records = [
            MockRecord({"schema_version": 1}),
            MockRecord({"schema_version": 2}),
        ]
        version_accessor = lambda r: r.document.get("schema_version")
        
        with pytest.raises(RuntimeError, match="multiple schema versions"):
            get_db_schema_version(records, version_accessor)

    def test_get_db_schema_version_non_integer_raises_error(self):
        """Raise TypeError if version is not integer."""
        records = [
            MockRecord({"schema_version": "1"}),  # String instead of int
        ]
        version_accessor = lambda r: r.document.get("schema_version")
        
        with pytest.raises(TypeError, match="Expected schema_version to be integer"):
            get_db_schema_version(records, version_accessor)

    def test_get_db_schema_version_version_zero(self):
        """Handle version 0 (baseline)."""
        records = [
            MockRecord({"schema_version": 0}),
            MockRecord({"schema_version": 0}),
        ]
        version_accessor = lambda r: r.document.get("schema_version")
        
        version = get_db_schema_version(records, version_accessor)
        assert version == 0


class MockMigration:
    """Mock migration module."""

    def __init__(self, forward_fn=None, schema=None):
        """Initialize mock migration."""
        self.forward_fn = forward_fn or (lambda doc: doc)
        self.schema = schema or {"type": "object"}

    def previous_schema(self):
        """Return previous schema."""
        return {"type": "object"}

    def target_schema(self):
        """Return target schema."""
        return self.schema

    def migrate_forward(self, doc):
        """Apply forward transformation."""
        return self.forward_fn(doc)


class TestValidateAllTransforms:
    """Tests for validate_all_transforms and apply_transforms."""

    def test_validate_all_transforms_all_valid(self):
        """All records pass validation."""
        records = [
            MockRecord({"schema_version": 1, "name": "Doc1"}),
            MockRecord({"schema_version": 1, "name": "Doc2"}),
        ]
        
        migration = MockMigration(
            forward_fn=lambda doc: {**doc, "schema_version": 2}
        )
        
        def mock_validate(doc, from_v, to_v, schema):
            return True, []
        
        doc_getter = lambda r: r.document
        
        success_count, failed_records = validate_all_transforms(
            records, migration, 1, 2, doc_getter, mock_validate
        )
        
        assert success_count == 2
        assert failed_records == []

    def test_validate_all_transforms_some_fail(self):
        """Some records fail validation."""
        records = [
            MockRecord({"schema_version": 1, "name": "Doc1"}),
            MockRecord({"schema_version": 1}),  # Missing "name"
        ]
        
        migration = MockMigration(
            forward_fn=lambda doc: {**doc, "schema_version": 2}
        )
        
        def mock_validate(doc, from_v, to_v, schema):
            # Fail if document missing "name"
            if "name" not in doc:
                return False, ["Missing name"]
            return True, []
        
        doc_getter = lambda r: r.document
        
        success_count, failed_records = validate_all_transforms(
            records, migration, 1, 2, doc_getter, mock_validate
        )
        
        assert success_count == 1
        assert len(failed_records) == 1

    def test_validate_all_transforms_uses_deepcopy(self):
        """validate_all_transforms does not modify original records."""
        original_doc = {"schema_version": 1, "name": "Doc1"}
        records = [MockRecord(deepcopy(original_doc))]
        
        migration = MockMigration(
            forward_fn=lambda doc: {**doc, "schema_version": 2, "new_field": "added"}
        )
        
        def mock_validate(doc, from_v, to_v, schema):
            return True, []
        
        doc_getter = lambda r: r.document
        
        validate_all_transforms(records, migration, 1, 2, doc_getter, mock_validate)
        
        # Original document should be unchanged
        assert records[0].document == original_doc
        assert "new_field" not in records[0].document

    def test_apply_transforms_modifies_records(self):
        """apply_transforms modifies records in-place."""
        records = [
            MockRecord({"schema_version": 1, "name": "Doc1"}),
            MockRecord({"schema_version": 1, "name": "Doc2"}),
        ]
        
        migration = MockMigration(
            forward_fn=lambda doc: {**doc, "schema_version": 2}
        )
        
        doc_getter = lambda r: r.document
        doc_setter = lambda r, doc: setattr(r, "document", doc)
        save_fn = lambda r: r.save(update_fields=["document"])
        
        apply_transforms(records, migration, doc_getter, doc_setter, save_fn)
        
        # All records should be transformed
        for record in records:
            assert record.document["schema_version"] == 2
            assert record.saved is True

    def test_apply_transforms_calls_save_with_update_fields(self):
        """apply_transforms calls save with update_fields kwarg."""
        records = [MockRecord({"schema_version": 1})]
        
        migration = MockMigration(
            forward_fn=lambda doc: {**doc, "schema_version": 2}
        )
        
        doc_getter = lambda r: r.document
        doc_setter = lambda r, doc: setattr(r, "document", doc)
        save_fn = lambda r: r.save(update_fields=["document"])
        
        apply_transforms(records, migration, doc_getter, doc_setter, save_fn)
        
        assert records[0].save_kwargs == {"update_fields": ["document"]}

    def test_validate_all_transforms_handles_migration_exception(self):
        """validate_all_transforms catches migration execution errors."""
        records = [MockRecord({"schema_version": 1})]
        
        def failing_migration(doc):
            raise ValueError("Intentional error")
        
        migration = MockMigration(forward_fn=failing_migration)
        
        def mock_validate(doc, from_v, to_v, schema):
            return True, []
        
        doc_getter = lambda r: r.document
        
        success_count, failed_records = validate_all_transforms(
            records, migration, 1, 2, doc_getter, mock_validate
        )
        
        assert success_count == 0
        assert len(failed_records) == 1
        assert "Intentional error" in failed_records[0][1]
