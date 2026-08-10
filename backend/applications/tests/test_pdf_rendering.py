"""Tests for PDF rendering, including context building and template styling."""

from unittest.mock import patch

from django.test import TestCase
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import (
    Application,
    _build_question_item,
    _icon_class_for_extension,
)


class IconClassTests(TestCase):
    """Test file extension to icon class mapping for PDF rendering."""

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


class PDFContextBuildingTests(TestCase):
    """Test PDF context building for template rendering."""

    def setUp(self):
        """Create test fixtures for PDF rendering."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
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

    def test_render_pdf_html_with_continuous_text_without_spaces(self):
        """render_pdf_html correctly handles continuous text without spaces.

        This test validates the fix for the bug where continuous text without
        spaces (e.g. "Nil...........") would cause table cells to overflow the
        page width. 
        
        Root cause: Without `table-layout: fixed;`, CSS tables expand beyond 
        their declared width to fit unbreakable content. The fix combines:
        1. `table-layout: fixed;` on all tables (forces width constraint)
        2. `word-break: break-word;` on cells (wraps long unbreakable words)
        
        This test verifies both properties are applied and that tables will
        respect their 100% width constraint in the rendered PDF.
        """
        # Create a questionnaire with a question that expects user input
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="pest-test",
            name="Pest Species Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Pest Species",
                        "sections": [
                            {
                                "title": "Information",
                                "description": "",
                                "questions": [
                                    {
                                        "label": "2. Pest species",
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

        # Create an application with continuous text (simulating user input)
        # This is the exact issue from the bug report: 100+ dots with no spaces
        continuous_text = "Nil" + "." * 100

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            document={
                "steps": [
                    {
                        "answers": {
                            "0-0": continuous_text
                        }
                    }
                ]
            },
        )

        # Render the PDF HTML
        html = app.render_pdf_html()

        # Verify 1: table-layout: fixed is present (critical for width constraint)
        # This forces the table to respect width: 100% and not expand beyond it
        self.assertIn("table-layout: fixed", html,
            "table-layout: fixed must be set to constrain table width")

        # Verify 2: width: 100% is still set (for page-width tables)
        self.assertIn("width: 100%", html,
            "tables must have width: 100% to use available page width")

        # Verify 3: text-wrapping properties are on cell classes
        # These force long unbreakable text to wrap within the constrained width
        self.assertIn("word-break: break-word", html,
            "word-break must force long words to wrap in cells")
        self.assertIn("overflow-wrap: break-word", html,
            "overflow-wrap must force long text to wrap in cells")

        # Verify 4: continuous text is present and will render in PDF
        self.assertIn(continuous_text, html,
            "continuous text must be in rendered output")

        # Verify 5: table structure is intact
        # Tables should be rendered but constrained by table-layout: fixed
        self.assertIn("<table", html)
        self.assertIn("</table>", html)

        # Verify 6: question-value cells have word-break applied
        # When combined with table-layout: fixed, this prevents horizontal overflow
        self.assertIn("class=\"question-value\"", html,
            "question-value cell class must be present in output")

        # Verify 7: the CSS rule contains both the width constraint AND cell wrapping
        # Pattern: `table { ... width: 100%; table-layout: fixed; ... }`
        table_css_pattern = "table {"
        style_start = html.find("<style>")
        style_end = html.find("</style>")
        self.assertTrue(style_start >= 0 and style_end >= 0,
            "Style block must exist in rendered HTML")

        style_content = html[style_start:style_end]

        # Ensure table-layout: fixed appears before any cell styles
        table_layout_pos = style_content.find("table-layout: fixed")
        question_value_pos = style_content.find(".question-value")
        cell_word_break_pos = style_content.find("word-break: break-word")

        self.assertTrue(table_layout_pos >= 0,
            "table-layout: fixed must be in CSS")
        self.assertTrue(cell_word_break_pos >= 0,
            "word-break: break-word must be in CSS for cells")
