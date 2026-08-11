"""Tests for PDF rendering, including context building and template styling."""

import uuid
from unittest.mock import Mock, PropertyMock, patch

from azure.core.exceptions import ResourceNotFoundError
from django.core.files.base import ContentFile
from django.test import TestCase
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import (
    Application,
    ApplicationAttachment,
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

    @patch('applications.models.os.path.exists')
    def test_build_question_item_for_image_missing_with_local_storage(self, mock_exists):
        """_build_question_item marks missing local image with is_missing=True and placeholder file_src."""
        # Simulate local file storage where file doesn't exist
        mock_attachment = Mock()
        mock_attachment.name = "photo.png"
        mock_attachment.key = "image-key-1"
        
        # .file.path returns a valid path string
        type(mock_attachment.file).path = PropertyMock(
            return_value="/media/attachments/photo.png"
        )
        # .file.url returns a valid URL for fallback
        type(mock_attachment.file).url = PropertyMock(
            return_value="https://example.com/media/photo.png"
        )
        # .file.size raises ResourceNotFoundError (fallback also fails)
        type(mock_attachment.file).size = PropertyMock(
            side_effect=ResourceNotFoundError("File not found in storage")
        )
        
        # Mock os.path.exists to return False (file doesn't exist in local storage)
        mock_exists.return_value = False

        attachments_by_key = {
            "image-key-1": mock_attachment,
        }

        question = {"type": "file", "label": "Upload Photos"}
        result = _build_question_item(question, ["image-key-1"], 0, attachments_by_key)

        # Image should be in image_files with placeholder path
        self.assertEqual(len(result["image_files"]), 1)
        self.assertEqual(len(result["other_files"]), 0)

        image_file = result["image_files"][0]
        self.assertEqual(image_file["name"], "photo.png")
        self.assertTrue(image_file["is_missing"], "is_missing flag must be True when local file doesn't exist")
        self.assertIn("image-not-found.png", image_file["file_src"], "file_src must include placeholder image")
        self.assertEqual(image_file["file_size"], "0\xa0bytes", "file_size must be 0 bytes when missing")

    def test_build_question_item_for_image_missing_with_azure_storage(self):
        """_build_question_item marks missing Azure blob with is_missing=True and placeholder file_src."""
        # Simulate Azure Blob Storage where .path raises NotImplementedError and .size raises ResourceNotFoundError
        mock_attachment = Mock()
        mock_attachment.name = "photo.png"
        mock_attachment.key = "image-key-2"
        
        # .file.path raises NotImplementedError (Azure backend doesn't support file:// paths)
        type(mock_attachment.file).path = PropertyMock(
            side_effect=NotImplementedError("Azure storage does not support file:// paths")
        )
        # .file.url returns a signed URL string (doesn't check if blob exists)
        type(mock_attachment.file).url = PropertyMock(
            return_value="https://azurestorage.blob.core.windows.net/container/blob.png?sig=..."
        )
        # .file.size raises ResourceNotFoundError when blob doesn't exist (triggers API call)
        type(mock_attachment.file).size = PropertyMock(
            side_effect=ResourceNotFoundError("Blob not found")
        )

        attachments_by_key = {
            "image-key-2": mock_attachment,
        }

        question = {"type": "file", "label": "Upload Photos"}
        result = _build_question_item(question, ["image-key-2"], 0, attachments_by_key)

        # Image should be in image_files with placeholder path
        self.assertEqual(len(result["image_files"]), 1, 
                         f"Expected 1 image file, got {len(result['image_files'])}. "
                         f"image_files={result['image_files']}, other_files={result['other_files']}")
        self.assertEqual(len(result["other_files"]), 0)

        image_file = result["image_files"][0]
        self.assertEqual(image_file["name"], "photo.png")
        self.assertTrue(image_file["is_missing"], "is_missing flag must be True when Azure blob doesn't exist")
        self.assertIn("image-not-found.png", image_file["file_src"], "file_src must include placeholder image")
        self.assertEqual(image_file["file_size"], "0\xa0bytes", "file_size must be 0 bytes when missing")

    @patch('applications.models.os.path.exists')
    @patch('applications.models.os.path.getsize')
    def test_build_question_item_for_image_existing_with_local_storage(self, mock_getsize, mock_exists):
        """_build_question_item correctly handles existing local image with file size."""
        mock_attachment = Mock()
        mock_attachment.name = "landscape.jpg"
        mock_attachment.key = "image-key-3"
        
        # .file.path returns a valid file path
        type(mock_attachment.file).path = PropertyMock(
            return_value="/media/attachments/2025-01/app123/landscape.jpg"
        )
        
        # Mock os.path.exists to return True (file exists)
        mock_exists.return_value = True
        # Mock os.path.getsize to return a file size
        mock_getsize.return_value = 1536000  # 1.5 MB

        attachments_by_key = {
            "image-key-3": mock_attachment,
        }

        question = {"type": "file", "label": "Upload Photos"}
        result = _build_question_item(question, ["image-key-3"], 0, attachments_by_key)

        self.assertEqual(len(result["image_files"]), 1)
        self.assertEqual(len(result["other_files"]), 0)

        image_file = result["image_files"][0]
        self.assertEqual(image_file["name"], "landscape.jpg")
        self.assertFalse(image_file["is_missing"], "is_missing should be False for existing file")
        self.assertTrue(image_file["file_src"].startswith("file://"), "file_src should be file:// URI for local storage")
        # File size should match the mocked size
        self.assertEqual(image_file["file_size"], "1.5\xa0MB", "file_size should be formatted correctly")

    def test_build_question_item_for_image_existing_with_azure_storage(self):
        """_build_question_item correctly handles existing Azure blob image with file size."""
        mock_attachment = Mock()
        mock_attachment.name = "diagram.png"
        mock_attachment.key = "image-key-4"
        
        # .file.path raises NotImplementedError (Azure doesn't support file paths)
        type(mock_attachment.file).path = PropertyMock(
            side_effect=NotImplementedError("Azure storage does not support file:// paths")
        )
        # .file.url returns a valid signed URL
        type(mock_attachment.file).url = PropertyMock(
            return_value="https://azurestorage.blob.core.windows.net/container/diagram.png?sig=..."
        )
        # .file.size returns the blob size (no exception = blob exists)
        type(mock_attachment.file).size = PropertyMock(return_value=1048576)  # 1 MB

        attachments_by_key = {
            "image-key-4": mock_attachment,
        }

        question = {"type": "file", "label": "Upload Photos"}
        result = _build_question_item(question, ["image-key-4"], 0, attachments_by_key)

        self.assertEqual(len(result["image_files"]), 1)
        self.assertEqual(len(result["other_files"]), 0)

        image_file = result["image_files"][0]
        self.assertEqual(image_file["name"], "diagram.png")
        self.assertFalse(image_file["is_missing"], "is_missing should be False for existing blob")
        self.assertEqual(image_file["file_src"], "https://azurestorage.blob.core.windows.net/container/diagram.png?sig=...", 
                         "file_src should be the blob URL")
        self.assertEqual(image_file["file_size"], "1.0\xa0MB", "file_size should be formatted as 1.0 MB")

    def test_build_question_item_for_non_image_file_existing(self):
        """_build_question_item correctly handles existing non-image file with file size."""
        mock_attachment = Mock()
        mock_attachment.name = "document.pdf"
        mock_attachment.key = "file-key-1"
        
        # .file.size returns file size (works for both local and Azure)
        type(mock_attachment.file).size = PropertyMock(return_value=2097152)  # 2 MB

        attachments_by_key = {
            "file-key-1": mock_attachment,
        }

        question = {"type": "file", "label": "Upload Documents"}
        result = _build_question_item(question, ["file-key-1"], 0, attachments_by_key)

        self.assertEqual(len(result["image_files"]), 0)
        self.assertEqual(len(result["other_files"]), 1)

        file_item = result["other_files"][0]
        self.assertEqual(file_item["name"], "document.pdf")
        self.assertEqual(file_item["extension"], "pdf")
        self.assertFalse(file_item["is_missing"], "is_missing should be False for existing file")
        self.assertEqual(file_item["file_size"], "2.0\xa0MB", "file_size should be formatted as 2.0 MB")
        self.assertEqual(file_item["icon_class"], "vscode-icons--file-type-pdf2", "PDF should have correct icon class")

    def test_build_question_item_for_non_image_file_missing_local_storage(self):
        """_build_question_item marks missing local non-image file with is_missing=True."""
        mock_attachment = Mock()
        mock_attachment.name = "spreadsheet.xlsx"
        mock_attachment.key = "file-key-2"
        
        # .file.size raises OSError when file is missing in local storage
        type(mock_attachment.file).size = PropertyMock(
            side_effect=OSError("File not found")
        )

        attachments_by_key = {
            "file-key-2": mock_attachment,
        }

        question = {"type": "file"}
        result = _build_question_item(question, ["file-key-2"], 0, attachments_by_key)

        self.assertEqual(len(result["other_files"]), 1)
        file_item = result["other_files"][0]
        self.assertEqual(file_item["name"], "spreadsheet.xlsx")
        self.assertTrue(file_item["is_missing"], "is_missing should be True when local file doesn't exist")
        self.assertEqual(file_item["file_size"], "0\xa0bytes", "file_size should be 0 bytes when missing")

    def test_build_question_item_for_non_image_file_missing_azure_storage(self):
        """_build_question_item marks missing Azure non-image file with is_missing=True."""
        mock_attachment = Mock()
        mock_attachment.name = "report.docx"
        mock_attachment.key = "file-key-3"
        
        # .file.size raises ResourceNotFoundError when blob doesn't exist in Azure
        type(mock_attachment.file).size = PropertyMock(
            side_effect=ResourceNotFoundError("Blob not found")
        )

        attachments_by_key = {
            "file-key-3": mock_attachment,
        }

        question = {"type": "file"}
        result = _build_question_item(question, ["file-key-3"], 0, attachments_by_key)

        self.assertEqual(len(result["other_files"]), 1)
        file_item = result["other_files"][0]
        self.assertEqual(file_item["name"], "report.docx")
        self.assertTrue(file_item["is_missing"], "is_missing should be True when Azure blob doesn't exist")
        self.assertEqual(file_item["file_size"], "0\xa0bytes", "file_size should be 0 bytes when missing")

    @patch('applications.models.os.path.exists')
    @patch('applications.models.os.path.getsize')
    def test_build_question_item_for_multiple_files_mixed_missing_existing(self, mock_getsize, mock_exists):
        """_build_question_item handles mix of existing and missing files correctly."""
        # Existing image
        mock_image = Mock()
        mock_image.name = "photo.jpg"
        mock_image.key = "img-1"
        type(mock_image.file).path = PropertyMock(return_value="/media/photo.jpg")
        type(mock_image.file).size = PropertyMock(return_value=512000)
        
        # Missing image - .path raises OSError; fallback Azure also fails
        mock_missing_image = Mock()
        mock_missing_image.name = "missing.png"
        mock_missing_image.key = "img-2"
        type(mock_missing_image.file).path = PropertyMock(side_effect=OSError("Not found"))
        type(mock_missing_image.file).url = PropertyMock(
            return_value="https://example.com/missing.png"
        )
        type(mock_missing_image.file).size = PropertyMock(
            side_effect=ResourceNotFoundError("Not found in storage")
        )
        
        # Existing non-image
        mock_doc = Mock()
        mock_doc.name = "contract.pdf"
        mock_doc.key = "file-1"
        type(mock_doc.file).size = PropertyMock(return_value=1024000)

        # Mock os.path.exists to return True (existing image file exists)
        # Note: This patches all calls to os.path.exists
        mock_exists.return_value = True
        # Mock os.path.getsize to return the size for the existing image
        mock_getsize.return_value = 512000

        attachments_by_key = {
            "img-1": mock_image,
            "img-2": mock_missing_image,
            "file-1": mock_doc,
        }

        question = {"type": "file"}
        result = _build_question_item(question, ["img-1", "img-2", "file-1"], 0, attachments_by_key)

        # Check image files: 1 existing + 1 missing
        self.assertEqual(len(result["image_files"]), 2)
        self.assertFalse(result["image_files"][0]["is_missing"])
        self.assertTrue(result["image_files"][1]["is_missing"])

        # Check other files: 1 existing document
        self.assertEqual(len(result["other_files"]), 1)
        self.assertFalse(result["other_files"][0]["is_missing"])

        # Verify file sizes
        self.assertEqual(result["image_files"][0]["file_size"], "500.0\xa0KB")
        self.assertEqual(result["image_files"][1]["file_size"], "0\xa0bytes")
        self.assertEqual(result["other_files"][0]["file_size"], "1000.0\xa0KB")


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

    def test_render_pdf_html_with_embedded_images_and_captions(self):
        """render_pdf_html displays embedded images with centre-aligned grey captions.

        This test verifies that:
        1. Embedded image files are rendered with their file names as captions
        2. Captions use the attachment-image-caption class
        3. Captions are centre-aligned (not left-aligned)
        4. Captions use a grey tone for visual hierarchy (not primary text colour)
        """
        # Create a questionnaire with a file upload question
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="images-test",
            name="Image Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Upload Images",
                        "sections": [
                            {
                                "title": "Images Section",
                                "description": "",
                                "questions": [
                                    {
                                        "label": "Attach images",
                                        "type": "file",
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

        # Create an application with embedded images
        # File names would be rendered as captions
        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            document={
                "steps": [
                    {
                        "answers": {
                            # File keys will be populated after creating attachments
                            "0-0": []
                        }
                    }
                ]
            },
        )

        # Create mock attachment objects with file information
        # Create first image attachment
        img1_key = uuid.uuid4()
        img1 = ApplicationAttachment.objects.create(
            application=app,
            key=img1_key,
            question="0-0",  # Question index
            name="screenshot-dashboard.png",
            file=ContentFile(b"fake png data", name="screenshot-dashboard.png"),
        )

        # Create second image attachment
        img2_key = uuid.uuid4()
        img2 = ApplicationAttachment.objects.create(
            application=app,
            key=img2_key,
            question="0-0",  # Question index
            name="form-filled-example.jpg",
            file=ContentFile(b"fake jpg data", name="form-filled-example.jpg"),
        )

        # Update the application document to reference the actual attachment keys
        app.document = {
            "steps": [
                {
                    "answers": {
                        "0-0": [str(img1_key), str(img2_key)]
                    }
                }
            ]
        }
        app.save()

        # Render the PDF HTML
        html = app.render_pdf_html()

        # Verify 1: Image captions are present with correct file names
        self.assertIn("screenshot-dashboard.png", html,
            "First image file name must appear in rendered output")
        self.assertIn("form-filled-example.jpg", html,
            "Second image file name must appear in rendered output")

        # Verify 2: Captions use the attachment-image-caption class
        self.assertIn("class=\"attachment-image-caption\"", html,
            "Image captions must use attachment-image-caption class")

        # Verify 3: The CSS includes text-align: center for captions
        style_start = html.find("<style>")
        style_end = html.find("</style>")
        self.assertTrue(style_start >= 0 and style_end >= 0,
            "Style block must exist in rendered HTML")

        style_content = html[style_start:style_end]

        # Find the .attachment-image-caption CSS rule
        caption_css_start = style_content.find(".attachment-image-caption")
        self.assertTrue(caption_css_start >= 0,
            "attachment-image-caption CSS rule must exist")

        # Find the next closing brace after the rule starts
        caption_css_end = style_content.find("}", caption_css_start)
        caption_css_block = style_content[caption_css_start:caption_css_end]

        # Verify text-align: center is in the CSS block
        self.assertIn("text-align: center", caption_css_block,
            "attachment-image-caption must have text-align: center")

        # Verify 4: Caption colour is grey (not black)
        # Grey colours are in the range #555-#999 or RGB(85-153, 85-153, 85-153)
        # We expect something like #666 or #777 or #888
        self.assertRegex(caption_css_block, r"color:\s*#[6-9a-f]{3}",
            "attachment-image-caption colour should be grey, not black")

        # Verify 5: word-break is still applied to captions
        self.assertIn("word-break: break-word", caption_css_block,
            "attachment-image-caption should still have word-break for long file names")

        # Verify 6: Image elements are rendered with correct structure
        self.assertIn("class=\"attachment-image\"", html,
            "Images must use attachment-image class")
        self.assertIn("attachment-group", html,
            "Images must be grouped in attachment-group")
        self.assertIn("Image attachments", html,
            "Section title for images must be present")
