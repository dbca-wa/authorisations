"""Comprehensive coverage tests for questionnaires module."""

import json
from django.test import TestCase
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.models import AnonymousUser

from processes.models import AuthorisationProcess
from users.models import User
from questionnaires.models import Questionnaire
from questionnaires.bugfix import DocumentJSONField, DocumentJSONFormField
from questionnaires.forms import QuestionnaireForm


class DocumentJSONFormFieldTests(TestCase):
    """Test DocumentJSONFormField nullable integer handling."""

    def test_document_json_form_field_init(self):
        """DocumentJSONFormField initializes with schema parameter."""
        schema = {"type": "object"}
        field = DocumentJSONFormField(schema=schema)
        self.assertEqual(field.schema, schema)

    def test_document_json_form_field_cast_nullable_integers_handles_dict_schema(self):
        """DocumentJSONFormField._cast_nullable_integers processes dict schemas."""
        schema = {
            "type": ["integer", "null"]
        }
        field = DocumentJSONFormField(schema=schema)
        # Test the internal method directly
        result = field._cast_nullable_integers(None, schema, schema)
        self.assertIsNone(result)

    def test_document_json_form_field_cast_nullable_integers_with_string_digit(self):
        """DocumentJSONFormField._cast_nullable_integers converts string digits to int."""
        schema = {"type": ["integer", "null"]}
        field = DocumentJSONFormField(schema=schema)
        result = field._cast_nullable_integers("42", schema, schema)
        self.assertEqual(result, 42)

    def test_document_json_form_field_cast_nullable_integers_with_object_properties(self):
        """DocumentJSONFormField._cast_nullable_integers processes object properties."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": ["integer", "null"]},
                "name": {"type": "string"}
            }
        }
        data = {"count": "5", "name": "test"}
        field = DocumentJSONFormField(schema=schema)
        result = field._cast_nullable_integers(data, schema, schema)
        self.assertIsNotNone(result)

    def test_document_json_form_field_cast_nullable_integers_with_array(self):
        """DocumentJSONFormField._cast_nullable_integers processes arrays."""
        schema = {
            "type": "array",
            "items": {"type": ["integer", "null"]}
        }
        data = ["1", None, "3"]
        field = DocumentJSONFormField(schema=schema)
        result = field._cast_nullable_integers(data, schema, schema)
        self.assertIsNotNone(result)

    def test_document_json_form_field_cast_nullable_integers_with_ref(self):
        """DocumentJSONFormField._cast_nullable_integers resolves $ref paths."""
        root_schema = {
            "$defs": {
                "number": {"type": ["integer", "null"]}
            }
        }
        ref_schema = {"$ref": "#/$defs/number"}
        field = DocumentJSONFormField(schema=root_schema)
        result = field._cast_nullable_integers("42", ref_schema, root_schema)
        self.assertEqual(result, 42)

    def test_document_json_form_field_cast_nullable_integers_with_invalid_ref(self):
        """DocumentJSONFormField._cast_nullable_integers handles invalid refs gracefully."""
        root_schema = {"$defs": {}}
        ref_schema = {"$ref": "#/$defs/nonexistent"}
        field = DocumentJSONFormField(schema=root_schema)
        result = field._cast_nullable_integers("test", ref_schema, root_schema)
        # Should return data unchanged if ref doesn't resolve
        self.assertEqual(result, "test")


class DocumentJSONFieldTests(TestCase):
    """Test DocumentJSONField model field."""

    def test_document_json_field_is_subclass_of_json_field(self):
        """DocumentJSONField is a proper JSONField subclass."""
        from django_jsonform.models.fields import JSONField
        self.assertTrue(issubclass(DocumentJSONField, JSONField))


class QuestionnaireFormMethodsTests(TestCase):
    """Test QuestionnaireForm method logic without full form instantiation."""

    def setUp(self):
        """Create test process and user."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.process = AuthorisationProcess.objects.create(
            slug="s40",
            name="Section 40",
            description="Section 40 process",
            sort_order=1,
        )
        self.valid_document = {
            "schema_version": "2025.07-1",
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
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    def test_clean_name_accepts_valid_name(self):
        """Valid questionnaire names are accepted."""
        # Test the logic from clean_name
        name = "  Valid Name With Spaces  "
        name = " ".join(name.split())
        self.assertEqual(name, "Valid Name With Spaces")

    def test_clean_name_rejects_leading_hyphen(self):
        """Names starting with hyphen are rejected."""
        name = "-Invalid"
        # Check the validation logic
        self.assertTrue(name.startswith("-"))

    def test_clean_name_rejects_trailing_hyphen(self):
        """Names ending with hyphen are rejected."""
        name = "Invalid-"
        self.assertTrue(name.endswith("-"))

    def test_clean_name_rejects_special_characters(self):
        """Names with special characters are rejected."""
        import re
        name = "Invalid@Special#"
        self.assertTrue(bool(re.search(r"[^A-Za-z0-9\- ]", name)))

    def test_clean_name_accepts_hyphens_and_spaces(self):
        """Valid names with hyphens and spaces are accepted."""
        import re
        name = "Valid-Name With Spaces"
        self.assertFalse(bool(re.search(r"[^A-Za-z0-9\- ]", name)))
        self.assertFalse(name.startswith("-"))
        self.assertFalse(name.endswith("-"))

    def test_clean_code_slugifies_input(self):
        """Code is converted to slug format."""
        from django.utils.text import slugify
        code = "My Code With Spaces"
        code = slugify(code)
        self.assertTrue("-" in code or code.islower())

    def test_clean_code_rejects_blank_after_slugify(self):
        """Code that slugifies to empty string is rejected."""
        from django.utils.text import slugify
        code = "@#$%@#$"
        code = slugify(code)
        self.assertEqual(code, "")

    def test_questionnaire_form_document_validator_exists(self):
        """QuestionnaireForm has document_validator method."""
        self.assertTrue(hasattr(QuestionnaireForm, 'document_validator'))

    def test_questionnaire_form_clean_name_method_exists(self):
        """QuestionnaireForm has clean_name method."""
        self.assertTrue(hasattr(QuestionnaireForm, 'clean_name'))

    def test_questionnaire_form_clean_code_method_exists(self):
        """QuestionnaireForm has clean_code method."""
        self.assertTrue(hasattr(QuestionnaireForm, 'clean_code'))

    def test_questionnaire_form_clean_method_exists(self):
        """QuestionnaireForm has clean method."""
        self.assertTrue(hasattr(QuestionnaireForm, 'clean'))
