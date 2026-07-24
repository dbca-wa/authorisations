"""Comprehensive coverage tests for applications.models module."""

from unittest.mock import MagicMock, Mock, patch
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile

from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import (
    Application,
    ApplicationStatus,
    ApplicationAttachment,
    _normalise_answer_value,
    _boolean_checkbox,
    _build_grid_rows,
    _build_question_item,
    _icon_class_for_extension,
    REVIEW_QUEUE_STATUSES,
    REVIEWER_SETTABLE_STATUSES,
)


class HelperFunctionsTests(TestCase):
    """Test module-level helper functions for PDF answer normalisation."""

    def test_boolean_checkbox_true(self):
        """_boolean_checkbox should return checked box for True."""
        self.assertEqual(_boolean_checkbox(True), "☑ Yes")

    def test_boolean_checkbox_false(self):
        """_boolean_checkbox should return unchecked box for False."""
        self.assertEqual(_boolean_checkbox(False), "☐ No")

    def test_normalise_answer_value_with_checkbox_type(self):
        """_normalise_answer_value handles checkbox type with boolean."""
        result = _normalise_answer_value({"type": "checkbox"}, True)
        self.assertEqual(result, "☑ Yes")

    def test_normalise_answer_value_with_bool_type_false(self):
        """_normalise_answer_value handles boolean False."""
        result = _normalise_answer_value({"type": "text"}, False)
        self.assertEqual(result, "☐ No")

    def test_normalise_answer_value_none_returns_none(self):
        """_normalise_answer_value returns None for None values."""
        result = _normalise_answer_value({"type": "text"}, None)
        self.assertIsNone(result)

    def test_normalise_answer_value_empty_string_returns_none(self):
        """_normalise_answer_value returns None for empty strings."""
        result = _normalise_answer_value({"type": "text"}, "")
        self.assertIsNone(result)

    def test_normalise_answer_value_list_with_items(self):
        """_normalise_answer_value flattens list to newline-separated string."""
        result = _normalise_answer_value({"type": "multiselect"}, ["a", "b", "c"])
        self.assertEqual(result, "a\nb\nc")

    def test_normalise_answer_value_empty_list_returns_none(self):
        """_normalise_answer_value returns None for empty lists."""
        result = _normalise_answer_value({"type": "multiselect"}, [])
        self.assertIsNone(result)

    def test_normalise_answer_value_dict_with_items(self):
        """_normalise_answer_value flattens dict to key: value lines."""
        result = _normalise_answer_value({"type": "object"}, {"key1": "val1", "key2": "val2"})
        # Dict order may vary, so check both values are present
        self.assertIn("key1: val1", result)
        self.assertIn("key2: val2", result)

    def test_normalise_answer_value_empty_dict_returns_none(self):
        """_normalise_answer_value returns None for empty dicts."""
        result = _normalise_answer_value({"type": "object"}, {})
        self.assertIsNone(result)

    def test_normalise_answer_value_string_passthrough(self):
        """_normalise_answer_value returns string values as-is."""
        result = _normalise_answer_value({"type": "text"}, "hello world")
        self.assertEqual(result, "hello world")

    def test_normalise_answer_value_number_passthrough(self):
        """_normalise_answer_value converts numbers to strings."""
        result = _normalise_answer_value({"type": "number"}, 42)
        self.assertEqual(result, "42")

    def test_normalise_answer_value_with_missing_question_type(self):
        """_normalise_answer_value handles question with no type."""
        result = _normalise_answer_value({}, "test")
        self.assertEqual(result, "test")

    def test_normalise_answer_value_with_none_question_dict(self):
        """_normalise_answer_value handles None question dict."""
        result = _normalise_answer_value(None, "test")
        self.assertEqual(result, "test")


class GridRowsTests(TestCase):
    """Test grid answer normalisation."""

    def test_build_grid_rows_with_valid_data(self):
        """_build_grid_rows builds rows from list of dicts."""
        question = {
            "type": "grid",
            "grid_columns": [
                {"label": "Column A"},
                {"label": "Column B"},
            ]
        }
        raw_value = [
            {"Column A": "A1", "Column B": "B1"},
            {"Column A": "A2", "Column B": "B2"},
        ]
        result = _build_grid_rows(question, raw_value)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ["A1", "B1"])
        self.assertEqual(result[1], ["A2", "B2"])

    def test_build_grid_rows_with_non_list_value(self):
        """_build_grid_rows returns empty list for non-list values."""
        question = {"grid_columns": [{"label": "Col"}]}
        result = _build_grid_rows(question, "not a list")
        self.assertEqual(result, [])

    def test_build_grid_rows_with_none_value(self):
        """_build_grid_rows returns empty list for None values."""
        question = {"grid_columns": [{"label": "Col"}]}
        result = _build_grid_rows(question, None)
        self.assertEqual(result, [])

    def test_build_grid_rows_with_non_dict_items(self):
        """_build_grid_rows skips non-dict items in row list."""
        question = {"grid_columns": [{"label": "Col"}]}
        raw_value = ["not a dict", {"Col": "value"}]
        result = _build_grid_rows(question, raw_value)
        self.assertEqual(len(result), 1)

    def test_build_grid_rows_with_missing_column_label(self):
        """_build_grid_rows uses default label when column label missing."""
        question = {"grid_columns": [{}]}
        raw_value = [{"Column": "value"}]
        result = _build_grid_rows(question, raw_value)
        # When column has no label, it gets "Column" as default.
        # But the row tries to find that key in the data dict.
        # Since the key doesn't match, it returns None for that cell
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 1)


class IconClassTests(TestCase):
    """Test file extension to icon class mapping."""

    def test_icon_class_for_pdf(self):
        """PDF extension maps to correct icon class."""
        result = _icon_class_for_extension("pdf")
        self.assertEqual(result, "vscode-icons--file-type-pdf2")

    def test_icon_class_for_doc(self):
        """DOC extension maps to Word icon."""
        result = _icon_class_for_extension("doc")
        self.assertEqual(result, "vscode-icons--file-type-word")

    def test_icon_class_for_docx(self):
        """DOCX extension maps to Word icon."""
        result = _icon_class_for_extension("docx")
        self.assertEqual(result, "vscode-icons--file-type-word")

    def test_icon_class_for_unknown_extension(self):
        """Unknown extension returns default icon class."""
        result = _icon_class_for_extension("xyz")
        self.assertEqual(result, "flat-color-icons--file")

    def test_icon_class_for_image_extensions(self):
        """Image extensions map to image icon."""
        for ext in ["jpg", "jpeg", "png"]:
            result = _icon_class_for_extension(ext)
            self.assertEqual(result, "flat-color-icons--image-file")


class QuestionItemBuilderTests(TestCase):
    """Test question payload building for PDF rendering."""

    def test_build_question_item_for_text_type(self):
        """_build_question_item creates correct payload for text question."""
        question = {"type": "text", "label": "Test Question"}
        result = _build_question_item(question, "answer text", 0, {})
        
        self.assertEqual(result["label"], "Test Question")
        self.assertEqual(result["type"], "text")
        self.assertEqual(result["value"], "answer text")

    def test_build_question_item_for_missing_label(self):
        """_build_question_item uses default label when missing."""
        question = {"type": "text"}
        result = _build_question_item(question, "value", 5, {})
        self.assertEqual(result["label"], "Question 6")

    def test_build_question_item_for_grid_type(self):
        """_build_question_item creates grid payload with rows."""
        question = {
            "type": "grid",
            "label": "Grid Question",
            "grid_columns": [
                {"label": "Col A"},
                {"label": "Col B"},
            ]
        }
        raw_value = [{"Col A": "A1", "Col B": "B1"}]
        result = _build_question_item(question, raw_value, 0, {})
        
        self.assertEqual(result["type"], "grid")
        self.assertEqual(result["grid_columns"], ["Col A", "Col B"])
        self.assertEqual(len(result["grid_rows"]), 1)

    def test_build_question_item_for_grid_type_with_default_column_label(self):
        """_build_question_item uses default column label when missing."""
        question = {
            "type": "grid",
            "grid_columns": [{}]  # Missing label
        }
        result = _build_question_item(question, [], 0, {})
        self.assertEqual(result["grid_columns"], ["Column"])

    def test_build_question_item_for_file_type_with_no_attachments(self):
        """_build_question_item handles file type with empty answer."""
        question = {"type": "file", "label": "Upload Files"}
        result = _build_question_item(question, [], 0, {})
        
        self.assertEqual(result["type"], "file")
        self.assertEqual(result["image_files"], [])
        self.assertEqual(result["other_files"], [])
        self.assertEqual(result["files"], [])

    def test_build_question_item_for_file_type_with_missing_attachment(self):
        """_build_question_item shows placeholder for missing attachments."""
        question = {"type": "file"}
        result = _build_question_item(question, ["missing-key"], 0, {})
        
        other_files = result["other_files"]
        self.assertEqual(len(other_files), 1)
        self.assertTrue(other_files[0]["is_missing"])
        self.assertIn("Missing file", other_files[0]["name"])


class ApplicationStatusTests(TestCase):
    """Test application status enums and constants."""

    def test_application_status_choices(self):
        """ApplicationStatus enum contains all required statuses."""
        expected_statuses = [
            "DRAFT", "DISCARDED", "SUBMITTED", "WITHDRAWN",
            "UNDER_REVIEW", "UNDER_ASSESSMENT",
            "APPROVED", "APPROVED_WITH_CONDITIONS", "DEFERRED", "REJECTED"
        ]
        for status in expected_statuses:
            self.assertTrue(hasattr(ApplicationStatus, status))

    def test_review_queue_statuses_constant(self):
        """REVIEW_QUEUE_STATUSES contains correct statuses."""
        expected = {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.UNDER_ASSESSMENT,
        }
        self.assertEqual(REVIEW_QUEUE_STATUSES, expected)

    def test_reviewer_settable_statuses_constant(self):
        """REVIEWER_SETTABLE_STATUSES contains correct statuses."""
        expected = {
            ApplicationStatus.DRAFT,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.UNDER_ASSESSMENT,
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.DEFERRED,
            ApplicationStatus.REJECTED,
        }
        self.assertEqual(REVIEWER_SETTABLE_STATUSES, expected)


class ApplicationModelTests(TestCase):
    """Test Application model methods."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.reviewer_user = User.objects.create_user(
            username="reviewer", password="testpass123"
        )
        self.process = AuthorisationProcess.objects.create(
            slug="s40",
            name="Section 40",
            description="Section 40 process",
            sort_order=1,
        )
        self.questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="new-app",
            name="New Application",
            description="New app form",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "description": "",
                        "sections": [
                            {
                                "title": "Section 1",
                                "description": "",
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
            },
            sort_order=1,
            created_by=self.user,
        )

    def test_application_str_representation(self):
        """Application __str__ method returns readable format."""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": [{"answers": {}}]},
        )
        expected = f"Application #{app.id} by testuser for New Application"
        self.assertEqual(str(app), expected)

    def test_application_internal_id_for_draft(self):
        """internal_id property generates correct format for draft."""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        # Draft has no submitted_at, so no date suffix
        expected = f"s40-new-app-{app.id}"
        self.assertEqual(app.internal_id, expected)

    def test_application_internal_id_for_submitted(self):
        """internal_id property includes date suffix for submitted apps."""
        from django.utils import timezone
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
        )
        # Get the formatted date
        date_suffix = app.submitted_at.strftime("/%y-%m")
        expected = f"s40-new-app-{app.id}{date_suffix}"
        self.assertEqual(app.internal_id, expected)

    def test_application_has_access_owner_access(self):
        """has_access returns True for application owner."""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        self.assertTrue(app.has_access(self.user))

    def test_application_has_access_unauthenticated_user(self):
        """has_access returns False for unauthenticated user."""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        # Create an unauthenticated user (is_authenticated=False is default for AnonymousUser)
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        self.assertFalse(app.has_access(anon))

    def test_application_has_access_reviewer_with_permissions(self):
        """has_access returns True for reviewer with process group."""
        # Create a group and add reviewer to it
        group = Group.objects.create(name="S40 Reviewers")
        self.reviewer_user.groups.add(group)
        
        # Add group to process assessor groups
        self.process.assessor_groups.add(group)
        
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        self.assertTrue(app.has_access(self.reviewer_user))

    def test_application_has_access_reviewer_without_permissions(self):
        """has_access returns False for reviewer without process group."""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        self.assertFalse(app.has_access(self.reviewer_user))

    @patch('applications.models.Application._load_pdf_icon_css')
    def test_build_pdf_context_empty_document(self, mock_load_css):
        """build_pdf_context handles empty application document."""
        mock_load_css.return_value = ""
        app = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )
        context = app.build_pdf_context()
        
        # Empty document should still have steps list (from questionnaire)
        self.assertIn("steps", context)

    def test_build_pdf_context_with_answers(self):
        """build_pdf_context builds correct structure with answers."""
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="renewal",
            name="Renewal",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
                                "description": "",
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
            },
            sort_order=1,
            created_by=self.user,
        )
        
        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            document={
                "steps": [
                    {
                        "answers": {
                            "0-0": "John Doe"
                        }
                    }
                ]
            },
        )
        
        context = app.build_pdf_context()
        
        # Check structure
        self.assertEqual(len(context["steps"]), 1)
        step = context["steps"][0]
        self.assertEqual(step["title"], "Step 1")
        self.assertEqual(len(step["sections"]), 1)
        
        section = step["sections"][0]
        self.assertEqual(section["prefix"], "A)")
        self.assertEqual(section["title"], "Section A")
        self.assertEqual(len(section["questions"]), 1)
        
        question = section["questions"][0]
        self.assertEqual(question["label"], "Name")
        self.assertEqual(question["value"], "John Doe")
