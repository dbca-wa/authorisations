"""E2E test: verify attachments dialog UI shows empty and populated states."""

from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from applications.models import Application, ApplicationAttachment


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_attachments_dialog_shows_empty_and_populated(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Create two reviewable applications (one empty, one with attachments) and
    verify the reviewer UI dialog renders empty and populated states respectively.
    """
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Find an existing submitted application owned by the other user (seeded)
    app_empty = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert app_empty is not None, "Expected a submitted application in seed data"

    # Create a new submitted application for the same owner that will hold attachments
    app_with_attachments = Application.objects.create(
        owner=other,
        questionnaire=app_empty.questionnaire,
        status="SUBMITTED",
        document=app_empty.document,
        submitted_at=timezone.now(),
    )

    # Add two attachments to the second application
    ApplicationAttachment.objects.create(
        application=app_with_attachments,
        question="0-0",
        name="fileA.txt",
        file=SimpleUploadedFile("fileA.txt", b"contentA", content_type="text/plain"),
    )

    ApplicationAttachment.objects.create(
        application=app_with_attachments,
        question="0-0",
        name="fileB.pdf",
        file=SimpleUploadedFile("fileB.pdf", b"%PDF-1.4\n", content_type="application/pdf"),
    )

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue and wait for cards to render
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    files_buttons = page.locator('button:has-text("Files")')
    # Expect at least two files buttons (one for existing submitted app, one for our new app)
    assert files_buttons.count() >= 2

    # Click the first Files button -> should correspond to the existing (older) submitted app with no attachments
    files_buttons.nth(0).click()
    page.wait_for_selector('role=dialog')
    # Empty-state message displayed in the dialog
    assert page.locator('text=Nothing to see here').count() >= 1

    # Close dialog
    page.get_by_label('close').click()

    # Click the second Files button -> our app with attachments
    files_buttons.nth(1).click()
    page.wait_for_selector('role=dialog')

    # Verify both attachments names are present in the dialog
    assert page.locator('text=fileA.txt').count() == 1
    assert page.locator('text=fileB.pdf').count() == 1

    # Tear down
    page.close()
    context.close()
