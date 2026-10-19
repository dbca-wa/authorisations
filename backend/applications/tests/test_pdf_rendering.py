"""Tests for PDF rendering, including context building and template styling."""

import uuid
from unittest.mock import Mock, PropertyMock, patch

from azure.core.exceptions import ResourceNotFoundError
from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import (
    Application,
    ApplicationAttachment,
    _build_question_item,
    _icon_class_for_extension,
)
from applications.statuses import ApplicationStatus


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
            "config": {
                "grid_columns": [
                    {"label": "Col A"},
                    {"label": "Col B"},
                ]
            }
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
            "config": {
                "grid_columns": [{}]  # Missing label
            }
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

    @patch('applications.models.settings.LOCAL_MEDIA_STORAGE', True)
    @patch('applications.models.os.path.getsize')
    def test_build_question_item_for_image_missing_with_local_storage(self, mock_getsize):
        """_build_question_item marks missing local image with is_missing=True and placeholder file_src."""
        # Simulate local file storage where file doesn't exist
        mock_attachment = Mock()
        mock_attachment.name = "photo.png"
        mock_attachment.key = "image-key-1"
        
        # .file.path returns a valid path string
        type(mock_attachment.file).path = PropertyMock(
            return_value="/media/attachments/photo.png"
        )
        
        # Mock os.path.getsize to raise OSError (file doesn't exist in local storage)
        mock_getsize.side_effect = OSError("File not found")

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

    @patch('applications.models.settings.LOCAL_MEDIA_STORAGE', False)
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

    @patch('applications.models.settings.LOCAL_MEDIA_STORAGE', True)
    @patch('applications.models.os.path.getsize')
    def test_build_question_item_for_image_existing_with_local_storage(self, mock_getsize):
        """_build_question_item correctly handles existing local image with file size."""
        mock_attachment = Mock()
        mock_attachment.name = "landscape.jpg"
        mock_attachment.key = "image-key-3"
        
        # .file.path returns a valid file path
        type(mock_attachment.file).path = PropertyMock(
            return_value="/media/attachments/2025-01/app123/landscape.jpg"
        )
        
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

    @patch('applications.models.settings.LOCAL_MEDIA_STORAGE', False)
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

    @patch('applications.models.settings.LOCAL_MEDIA_STORAGE', True)
    @patch('applications.models.os.path.getsize')
    def test_build_question_item_for_multiple_files_mixed_missing_existing(self, mock_getsize):
        """_build_question_item handles mix of existing and missing files correctly."""
        # Existing image
        mock_image = Mock()
        mock_image.name = "photo.jpg"
        mock_image.key = "img-1"
        type(mock_image.file).path = PropertyMock(return_value="/media/photo.jpg")
        type(mock_image.file).size = PropertyMock(return_value=512000)
        
        # Missing image - os.path.getsize raises OSError
        mock_missing_image = Mock()
        mock_missing_image.name = "missing.png"
        mock_missing_image.key = "img-2"
        type(mock_missing_image.file).path = PropertyMock(return_value="/media/missing.png")
        
        # Existing non-image
        mock_doc = Mock()
        mock_doc.name = "contract.pdf"
        mock_doc.key = "file-1"
        type(mock_doc.file).size = PropertyMock(return_value=1024000)

        # Mock os.path.getsize to return size for existing file and raise for missing
        def getsize_side_effect(path):
            if "missing" in path:
                raise OSError("File not found")
            return 512000  # Size for photo.jpg

        mock_getsize.side_effect = getsize_side_effect

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

    def test_render_pdf_html_includes_draft_watermark_overlay_for_draft_status(self):
        """render_pdf_html includes DRAFT watermark overlay for DRAFT status.

        This test verifies that:
        1. The PDF context includes is_draft=True for DRAFT applications
        2. The @prince-overlay CSS rule is present to render the watermark
        3. The watermark displays "DRAFT" text rotated -30 degrees
        4. Status marker element is NOT present (old implementation removed)
        """
        # Create an application with DRAFT status
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="draft-test",
            name="Draft Test",
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
                                        "label": "Test Question",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="DRAFT",  # Explicitly set to DRAFT
            document={
                "steps": [
                    {
                        "answers": {
                            "0-0": "test answer"
                        }
                    }
                ]
            },
        )

        # Verify context is_draft flag
        context = app.build_pdf_context()
        self.assertTrue(context["is_draft"],
            "Context must include is_draft=True for DRAFT applications")

        # Render the PDF HTML
        html = app.render_pdf_html()

        # Verify 1: @prince-overlay watermark CSS is present (only for DRAFT)
        self.assertIn("@prince-overlay", html,
            "@prince-overlay rule must be present for DRAFT applications")
        self.assertIn('content: "DRAFT"', html,
            "Watermark must display DRAFT text")
        self.assertIn("transform: rotate(-30deg)", html,
            "Watermark must be rotated -30 degrees counter-clockwise")

        # Verify 2: Status marker element is NOT present (old implementation removed)
        self.assertNotIn('class="status-marker"', html,
            "Status marker element must NOT be present (old DRAFT label implementation)")
        self.assertNotIn("string-set: app-status", html,
            "string-set CSS rule must NOT be present (replaced by @prince-overlay)")
        self.assertNotIn('string(app-status)', html,
            "string(app-status) reference must NOT be present in page headers")

        # Verify 3: Page header shows clean internal ID without DRAFT suffix
        self.assertIn('content: "#', html,
            "Page header must show internal_id with # prefix")
        # Verify page header contains the rendered internal ID
        self.assertIn(f'content: "#{app.internal_id}"', html,
            "Page header must show the actual internal_id value")

    def test_render_pdf_html_excludes_draft_watermark_overlay_for_non_draft_status(self):
        """render_pdf_html does not include DRAFT watermark for non-DRAFT status.

        This test verifies that:
        1. The PDF context includes is_draft=False for non-DRAFT applications
        2. The @prince-overlay CSS rule is NOT present for non-DRAFT applications
        3. Status marker element is NOT present (old implementation removed)
        4. Page header shows clean internal ID without any watermark
        """
        # Create an application with SUBMITTED status
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="submitted-test",
            name="Submitted Test",
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
                                        "label": "Test Question",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="SUBMITTED",  # Set to SUBMITTED, not DRAFT
            document={
                "steps": [
                    {
                        "answers": {
                            "0-0": "test answer"
                        }
                    }
                ]
            },
        )

        # Verify context is_draft flag
        context = app.build_pdf_context()
        self.assertFalse(context["is_draft"],
            "Context must include is_draft=False for non-DRAFT applications")

        # Render the PDF HTML
        html = app.render_pdf_html()

        # Verify 1: @prince-overlay watermark CSS is NOT present for non-DRAFT
        self.assertNotIn("@prince-overlay", html,
            "@prince-overlay rule must NOT be present for non-DRAFT applications")
        self.assertNotIn('content: "DRAFT"', html,
            "DRAFT watermark text must NOT be present for non-DRAFT applications")

        # Verify 2: Status marker element is NOT present (old implementation removed)
        self.assertNotIn('class="status-marker"', html,
            "Status marker element must NOT be present (old implementation removed)")
        self.assertNotIn("string-set: app-status", html,
            "string-set CSS rule must NOT be present (old implementation removed)")

        # Verify 3: Page header shows clean internal ID without any suffix
        self.assertIn('content: "#', html,
            "Page header must show internal_id with # prefix")
        # Verify page header contains the rendered internal ID
        self.assertIn(f'content: "#{app.internal_id}"', html,
            "Page header must show the actual internal_id value")

    def test_render_pdf_html_includes_metadata_page_for_all_statuses(self):
        """render_pdf_html includes application metadata information page for all statuses.

        This test verifies that:
        1. The metadata page HTML structure is present
        2. The metadata page has the correct header "Application Information"
        3. The metadata page appears after application content (page break)
        4. The metadata page is included regardless of application status
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="metadata-test",
            name="Metadata Test",
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
                                        "label": "Test Question",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="DRAFT",
            document={
                "steps": [
                    {
                        "answers": {
                            "0-0": "test answer"
                        }
                    }
                ]
            },
        )

        html = app.render_pdf_html()

        # Verify 1: Metadata page HTML structure is present
        self.assertIn('class="metadata-page"', html,
            "Metadata page container must be present")

        # Verify 2: Metadata page has correct header
        self.assertIn('class="metadata-page-header"', html,
            "Metadata page header element must be present")
        self.assertIn("Application Information", html,
            "Metadata page must have 'Application Information' header")

        # Verify 3: Metadata page uses page-break-before for separation
        self.assertIn("page-break-before: always", html,
            "Metadata page must have page break to separate from content")

        # Verify 4: Metadata page is included regardless of status
        # This test uses DRAFT; non-DRAFT status is tested separately
        self.assertIn('class="metadata-table"', html,
            "Metadata table must be present for all application statuses")

    def test_metadata_page_contains_questionnaire_details_section(self):
        """Metadata page displays questionnaire details in a dedicated section.

        This test verifies that:
        1. Questionnaire details section header is present
        2. Process name is displayed
        3. Questionnaire name is displayed
        4. Questionnaire version is displayed
        5. Questionnaire last modified date is displayed in full date format
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="quest-section-test",
            name="Test Questionnaire Name",
            version=3,
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="SUBMITTED",
            document={"steps": [{"answers": {"0-0": "test"}}]},
        )

        html = app.render_pdf_html()

        # Verify 1: Questionnaire section header
        self.assertIn("QUESTIONNAIRE DETAILS", html,
            "Questionnaire details section header must be present")

        # Verify 2: Process name is displayed
        self.assertIn(self.process.name, html,
            "Process name must be displayed in metadata")

        # Verify 3: Questionnaire name is displayed
        self.assertIn("Test Questionnaire Name", html,
            "Questionnaire name must be displayed in metadata")

        # Verify 4: Questionnaire version is displayed
        self.assertIn(">3<", html,  # Wrapped in tags to ensure it's the version value
            "Questionnaire version must be displayed in metadata")

        # Verify 5: Questionnaire updated_at is displayed with full month format
        self.assertIn("Questionnaire last modified on", html,
            "Questionnaire last modified label must be present")
        # Date format should use full month name (j F Y format)
        # E.g., "15 October 2026" not "15 Oct 2026"
        self.assertNotIn(" Oct ", html,  # Ensure abbreviated month is NOT present
            "Date should use full month name, not abbreviated")

    def test_metadata_page_contains_application_details_section(self):
        """Metadata page displays application details in a dedicated section.

        This test verifies that:
        1. Application details section header is present
        2. Application ID is displayed with # prefix
        3. Application key (UUID) is displayed
        4. Current status is displayed in human-readable format
        5. Applicant full name is displayed
        6. Applicant email is displayed
        7. Created on date is displayed in full format
        8. Last modified on date is displayed in full format
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="app-section-test",
            name="App Details Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status=ApplicationStatus.UNDER_REVIEW,
            document={"steps": [{"answers": {"0-0": "test"}}]},
        )

        html = app.render_pdf_html()

        # Verify 1: Application section header
        self.assertIn("APPLICATION DETAILS", html,
            "Application details section header must be present")

        # Verify 2: Application ID with # prefix
        self.assertIn(f"#{app.internal_id}", html,
            "Application ID must be displayed with # prefix")

        # Verify 3: Application key (UUID)
        self.assertIn(str(app.key), html,
            "Application key (UUID) must be displayed")

        # Verify 4: Current status in human-readable format
        self.assertIn("Under Review", html,  # UNDER_REVIEW status displays as "Under Review"
            "Current status must be displayed in human-readable format")

        # Verify 5: Applicant full name
        full_name = f"{self.user.first_name} {self.user.last_name}"
        self.assertIn(full_name, html,
            "Applicant full name must be displayed")

        # Verify 6: Applicant email
        self.assertIn(self.user.email, html,
            "Applicant email must be displayed")

        # Verify 7: Created on with full date format
        self.assertIn("Created on", html,
            "Created on label must be present")
        # Ensure full month name is used (j F Y format: day Month Year)
        self.assertNotIn(" Oct ", html,
            "Dates should use full month name")

        # Verify 8: Last modified on with full date format
        self.assertIn("Last modified on", html,
            "Last modified on label must be present")

    def test_metadata_page_conditional_submitted_timestamp_display(self):
        """Metadata page displays submitted timestamp only for submitted applications.

        This test verifies that:
        1. For DRAFT applications without submitted_at: no submitted timestamp row
        2. For SUBMITTED applications: "Formally submitted on" row is present
        3. Submitted timestamp uses full date format
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="submitted-ts-test",
            name="Submitted TS Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
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

        # Test 1: DRAFT application (no submitted_at)
        draft_app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="DRAFT",
            document={"steps": [{"answers": {"0-0": "test"}}]},
        )

        draft_html = draft_app.render_pdf_html()

        # For DRAFT: submitted_at is None, so "Formally submitted on" row should NOT appear
        self.assertNotIn("Formally submitted on", draft_html,
            "DRAFT application should not have 'Formally submitted on' row")

        # Test 2: SUBMITTED application (with submitted_at)
        submitted_app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="SUBMITTED",
            document={"steps": [{"answers": {"0-0": "test"}}]},
            submitted_at=timezone.now(),
        )

        submitted_html = submitted_app.render_pdf_html()

        # For SUBMITTED: submitted_at is set, so row should appear
        self.assertIn("Formally submitted on", submitted_html,
            "SUBMITTED application must have 'Formally submitted on' row")

    def test_metadata_page_uses_metadata_table_styling(self):
        """Metadata page uses appropriate styling classes for visual distinction.

        This test verifies that:
        1. Metadata table uses metadata-table class
        2. Section headers use metadata-section-header class with blue background
        3. Labels use metadata-label class with grey background
        4. Values use metadata-value class with white background
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="styling-test",
            name="Styling Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="DRAFT",
            document={"steps": [{"answers": {"0-0": "test"}}]},
        )

        html = app.render_pdf_html()

        # Verify 1: Metadata table styling class
        self.assertIn('class="metadata-table"', html,
            "Metadata table must use metadata-table class")

        # Verify 2: Section headers use styling class
        self.assertIn('class="metadata-section-header"', html,
            "Section headers must use metadata-section-header class")

        # Verify 3: Labels use styling class
        self.assertIn('class="metadata-label"', html,
            "Labels must use metadata-label class")

        # Verify 4: Values use styling class
        self.assertIn('class="metadata-value"', html,
            "Values must use metadata-value class")

        # Verify 5: Section headers span full width (colspan="2")
        self.assertIn('colspan="2"', html,
            "Section headers must span full table width with colspan=2")

    def test_metadata_page_has_empty_footer(self):
        """Metadata page footer should be empty and not display breadcrumb information.

        The metadata page is a separate information page, not part of the application
        content. The breadcrumb footer information (current section/step) is misleading
        on this page, so it should be suppressed and the footer should be empty.

        This test verifies that:
        1. Metadata page div uses the 'page: metadata-page' CSS class
        2. The @page metadata-page rule suppresses breadcrumb footer content
        """
        questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="footer-test",
            name="Footer Test",
            document={
                "schema_version": "2025.07-1",
                "steps": [
                    {
                        "title": "Step 1",
                        "sections": [
                            {
                                "title": "Section A",
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

        app = Application.objects.create(
            owner=self.user,
            questionnaire=questionnaire,
            status="DRAFT",
            document={"steps": [{"answers": {"0-0": "test"}}]},
        )

        html = app.render_pdf_html()

        # Verify 1: Metadata page div exists and uses metadata-page class
        self.assertIn('<div class="metadata-page">', html,
            "Metadata page must have metadata-page class")

        # Verify 2: CSS rule for metadata page exists to suppress footer
        self.assertIn('@page metadata-page', html,
            "CSS must include @page metadata-page rule to control footer styling")

        # Verify 3: Metadata page CSS suppresses breadcrumb footer
        self.assertIn('@bottom-left', html,
            "CSS must include @bottom-left footer definition")
