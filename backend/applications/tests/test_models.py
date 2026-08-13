"""Comprehensive coverage tests for applications.models module."""

from django.contrib.auth.models import Group, AnonymousUser
from django.test import TestCase
from django.utils import timezone
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import (
    Application,
    _boolean_checkbox,
    _build_grid_rows,
    _normalise_answer_value,
)
from applications.statuses import (
    REVIEW_QUEUE_STATUSES,
    REVIEWER_SETTABLE_STATUSES,
    ApplicationStatus,
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
        anon = AnonymousUser()
        self.assertFalse(app.has_access(anon))

    def test_application_has_access_reviewer_with_permissions(self):
        """has_access returns True for reviewer with process group."""
        # Create a group and add reviewer to it
        group = Group.objects.create(name="S40 Reviewers")
        self.reviewer_user.groups.add(group)
        
        # Add group to process assessor groups
        self.process.reviewer_groups.add(group)
        
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


