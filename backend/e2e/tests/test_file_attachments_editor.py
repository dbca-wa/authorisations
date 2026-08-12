"""E2E tests for file attachment rendering on draft editor pages.

This module validates that uploaded attachment tiles render correctly,
including filename visibility, icon display for supported file types,
and file size information in human-readable format.
"""

import pytest
from applications.models import Application, ApplicationAttachment
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_draft_editor_file_attachments_render_icons_for_supported_types(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify draft editor attachment tiles render visible icons per file type.

    Scenario steps:
    1. Use seeded draft application with a single file question.
    2. Add image/png, pdf, and xlsx attachments.
    3. Confirm the application appears on My Applications by internal_id.
    4. Open the draft editor URL for the same application.
    5. Confirm all three filenames are visible.
    6. Confirm each icon element is visible and has non-zero dimensions.
    """
    owner = e2e_users["other"]
    application = Application.objects.select_related("questionnaire", "questionnaire__process").get(
        owner=owner,
        key="00000000-0000-4000-8000-000000000003",
        status="DRAFT",
    )

    question_key = "0.0-0"
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="image.png",
        file=SimpleUploadedFile("image.png", b"fake-png-content", content_type="image/png"),
    )
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="document.pdf",
        file=SimpleUploadedFile("document.pdf", b"%PDF-1.4\n", content_type="application/pdf"),
    )
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="data.xlsx",
        file=SimpleUploadedFile(
            "data.xlsx",
            b"PK\x03\x04fake-xlsx-content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    )

    context = authenticated_browser_context_factory(owner)
    page = context.new_page()

    def assert_attachment_icon_renders(filename: str, expected_icon_class: str):
        """Assert the icon for a specific attachment filename is rendered visibly.

        The icon must be present in the same tile as the filename, have non-zero
        dimensions, and expose a resolved background image in computed styles.
        """
        tile = page.locator(f"text={filename}").locator("xpath=ancestor::a[1]")
        assert tile.count() >= 1, f"Expected attachment tile for '{filename}'"

        icon = tile.locator(f"span.{expected_icon_class}").first
        assert icon.is_visible(timeout=5000), (
            f"Expected icon '{expected_icon_class}' to be visible for '{filename}'"
        )

        bbox = icon.bounding_box()
        assert bbox is not None, f"Icon '{expected_icon_class}' should have a bounding box"
        assert bbox["width"] > 0, (
            f"Icon '{expected_icon_class}' width should be > 0 for '{filename}', got {bbox['width']}"
        )
        assert bbox["height"] > 0, (
            f"Icon '{expected_icon_class}' height should be > 0 for '{filename}', got {bbox['height']}"
        )

        background_image = icon.evaluate(
            "element => window.getComputedStyle(element).backgroundImage"
        )
        assert background_image and background_image != "none", (
            f"Icon '{expected_icon_class}' background image should resolve for '{filename}', got '{background_image}'"
        )

    try:
        page.goto("/my-applications")
        page.wait_for_load_state("networkidle", timeout=5000)

        application_id_locator = page.locator(f"text={application.internal_id}")
        assert application_id_locator.count() >= 1, (
            f"Expected application internal_id '{application.internal_id}' to be visible in My Applications"
        )

        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        assert page.locator("text=image.png").count() >= 1
        assert page.locator("text=document.pdf").count() >= 1
        assert page.locator("text=data.xlsx").count() >= 1

        assert_attachment_icon_renders("image.png", "flat-color-icons--image-file")
        assert_attachment_icon_renders("document.pdf", "vscode-icons--file-type-pdf2")
        assert_attachment_icon_renders("data.xlsx", "vscode-icons--file-type-excel")
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_draft_editor_attachment_tiles_display_file_size_in_human_readable_format(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify draft editor attachment tiles display file sizes in human-readable format.

    Scenario steps:
    1. Use seeded draft application with a single file question.
    2. Add attachments with various file sizes (small, medium, large).
    3. Open the draft editor URL for the application.
    4. Confirm all three filenames and formatted file sizes are visible.
    5. Verify sizes display correctly: bytes for small files, KB/MB for larger files.
    """
    owner = e2e_users["other"]
    application = Application.objects.select_related("questionnaire", "questionnaire__process").get(
        owner=owner,
        key="00000000-0000-4000-8000-000000000003",
        status="DRAFT",
    )

    question_key = "0.0-0"
    # Create attachments with different sizes for formatting verification
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="small.txt",
        file=SimpleUploadedFile("small.txt", b"tiny" * 50, content_type="text/plain"),
        size=200,  # 200 bytes
    )
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="medium.pdf",
        file=SimpleUploadedFile("medium.pdf", b"%PDF-1.4\n" + b"x" * 5000, content_type="application/pdf"),
        size=5120,  # 5 KB
    )
    ApplicationAttachment.objects.create(
        application=application,
        question=question_key,
        name="large.xlsx",
        file=SimpleUploadedFile("large.xlsx", b"PK\x03\x04" + b"x" * 102400, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        size=102400,  # ~100 KB
    )

    context = authenticated_browser_context_factory(owner)
    page = context.new_page()

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        # Verify all filenames are present
        assert page.locator("text=small.txt").count() >= 1
        assert page.locator("text=medium.pdf").count() >= 1
        assert page.locator("text=large.xlsx").count() >= 1

        # Verify formatted file sizes are displayed
        # 200 bytes should display as "200 B"
        assert page.locator("text=200 B").count() >= 1, (
            "Expected file size '200 B' to be displayed for small.txt"
        )
        
        # 5 KB should display as "5 KB"
        assert page.locator("text=5 KB").count() >= 1, (
            "Expected file size '5 KB' to be displayed for medium.pdf"
        )
        
        # ~100 KB should display with proper formatting
        assert page.locator("text=/100(\\.[0-9])? KB/").count() >= 1, (
            "Expected file size to display as '100 KB' or similar for large.xlsx"
        )
    finally:
        page.close()
        context.close()
