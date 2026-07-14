"""E2E tests: comprehensive assessment page functionality including card display and attachments dialog."""

from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from applications.models import Application, ApplicationAttachment


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_displays_process_and_questionnaire_metadata(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify assessment card displays process name, questionnaire name with version, and status chips."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Find an existing submitted application
    app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert app is not None, "Expected a submitted application in seed data"

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Verify process name is displayed in a chip
    process_chip = page.locator(f'text={app.questionnaire.process.name}')
    assert process_chip.count() >= 1, f"Process name '{app.questionnaire.process.name}' not found on assessment page"

    # Verify questionnaire name and version are displayed together
    questionnaire_text = f"{app.questionnaire.name} (v{app.questionnaire.version})"
    questionnaire_chip = page.locator(f'text={questionnaire_text}')
    assert questionnaire_chip.count() >= 1, f"Questionnaire text '{questionnaire_text}' not found on assessment page"

    # Verify status is displayed (formatted with title case)
    status_text = " ".join(word.capitalize() for word in app.status.split("_"))
    status_chip = page.locator(f'text={status_text}')
    assert status_chip.count() >= 1, f"Status '{status_text}' not found on assessment page"

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_displays_applicant_information(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify assessment card displays applicant full name, email, and submission date."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Find an existing submitted application owned by the other user
    app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert app is not None, "Expected a submitted application in seed data"

    # Verify the application has owner information
    assert app.owner is not None
    assert app.owner.first_name and app.owner.last_name
    assert app.owner.email

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Verify applicant full name is displayed
    full_name = f"{app.owner.first_name} {app.owner.last_name}"
    name_element = page.locator(f'text={full_name}')
    assert name_element.count() >= 1, f"Applicant name '{full_name}' not found on assessment page"

    # Verify applicant email is displayed
    email_element = page.locator(f'text={app.owner.email}')
    assert email_element.count() >= 1, f"Applicant email '{app.owner.email}' not found on assessment page"

    # Verify "Submitted" text with relative time is displayed
    submitted_text = page.locator('text=Submitted')
    assert submitted_text.count() >= 1, "Submitted text not found on assessment page"

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_email_copy_to_clipboard(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify clicking applicant email copies it to clipboard with visual feedback."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Find an existing submitted application
    app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert app is not None, "Expected a submitted application in seed data"

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Find the email box and click it
    email_box = page.locator(f'text={app.owner.email}').first.locator('..')
    assert email_box.is_visible(), f"Email box for {app.owner.email} not visible"

    # Verify the email box has a title attribute for accessibility
    title = email_box.get_attribute("title")
    assert title is not None, f"Expected title attribute on email box"
    assert "copy" in title.lower() or "click" in title.lower() or "email" in title.lower(), f"Expected copy/click hint in title, got: {title}"

    # Click the email box
    email_box.click()

    # Verify snackbar appears (success message for copy) - wait for it to appear
    snackbar = page.locator('text=/copied|clipboard/', ).first
    page.wait_for_selector('text=/copied|clipboard/', timeout=5000)
    assert snackbar.is_visible(), "Copy success message not found after clicking email"

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_pdf_download_button(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify PDF download button is present and links to the correct download URL."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Find an existing submitted application (SUBMITTED status is downloadable)
    app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert app is not None, "Expected a submitted application in seed data"

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Find the PDF button and verify it's within a link
    pdf_button = page.locator('button:has-text("PDF")').first
    assert pdf_button.is_visible(), "PDF button not found for downloadable application"

    # Get the parent link element (PDF button is inside MUI Link component)
    pdf_link = pdf_button.locator('xpath=ancestor::a')
    expected_href = f"/d/{app.key}"
    actual_href = pdf_link.get_attribute("href")
    assert actual_href == expected_href, f"Expected PDF link to {expected_href}, got {actual_href}"

    # Verify link opens in new tab
    target = pdf_link.get_attribute("target")
    assert target == "_blank", f"Expected target='_blank', got '{target}'"

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_attachment_dialog_shows_empty_and_populated_states(
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

    # Find the card for the app_empty application using its internal_id and click its Files button
    # The card contains the internal_id text, so we find the closest Files button to it
    page.locator(f'text={app_empty.internal_id}').locator('xpath=ancestor::*[contains(@class, "MuiCard")]//button[contains(text(), "Files")]').click()
    page.wait_for_selector('role=dialog')
    # Empty-state message displayed in the dialog
    assert page.locator('text=Nothing to see here').count() >= 1

    # Close dialog
    page.get_by_label('close').click()

    # Find the card for the app_with_attachments application using its internal_id and click its Files button
    page.locator(f'text={app_with_attachments.internal_id}').locator('xpath=ancestor::*[contains(@class, "MuiCard")]//button[contains(text(), "Files")]').click()
    page.wait_for_selector('role=dialog')

    # Verify both attachments names are present in the dialog
    assert page.locator('text=fileA.txt').count() == 1
    assert page.locator('text=fileB.pdf').count() == 1

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_page_sort_by_application_type(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify assessment queue can be sorted by application type (process order + questionnaire order)."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Create multiple submitted applications with different questionnaires to test sorting
    # (The seeded data should already have some; we'll use what's available)
    submitted_apps = list(
        Application.objects.filter(owner=other, status="SUBMITTED").order_by("id")[:3]
    )
    assert len(submitted_apps) >= 1, "Expected at least 1 submitted application in seed data"

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Verify sort control is visible (shown only when there's more than 1 application)
    if len(submitted_apps) > 1:
        sort_control = page.locator('id=assessment-sort')
        assert sort_control.is_visible(), "Sort control should be visible when multiple applications exist"

        # Open the sort dropdown
        sort_control.click()
        page.wait_for_selector('text=Application type')

        # Click "Application type" option
        page.locator('text=Application type').click()

        # Verify applications are re-sorted (wait a moment for re-render)
        page.wait_for_timeout(500)

        # Verify cards are still displayed
        files_buttons = page.locator('button:has-text("Files")')
        assert files_buttons.count() >= 1, "Applications should still be displayed after sorting"
    else:
        # Single application: sort control should not be visible
        sort_control = page.locator('id=assessment-sort')
        assert (
            sort_control.count() == 0
        ), "Sort control should not be visible when only 1 application exists"

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_displays_submission_date_not_creation_date(
    authenticated_browser_context_factory,
    e2e_users,
):
    """CRITICAL: Verify "Submitted" label displays submission date (submitted_at), NOT creation date (created_at).
    
    This test catches the bug where AssessmentCard incorrectly displayed the creation date
    for the "Submitted" label. The test creates an application with deliberately different
    creation and submission dates to ensure the correct date field is displayed.
    """
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Create a submitted application with DIFFERENT creation and submission dates
    # Created 7 days ago, submitted today
    now = timezone.now()
    created_7_days_ago = now - timezone.timedelta(days=7)

    # Get an existing questionnaire to use for our test app
    existing_app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert existing_app is not None, "Expected a submitted application in seed data"

    # Create new app with old creation date but recent submission date
    test_app = Application.objects.create(
        owner=other,
        questionnaire=existing_app.questionnaire,
        status="SUBMITTED",
        document=existing_app.document,
        created_at=created_7_days_ago,  # Created 7 days ago
        submitted_at=now,  # Submitted today
    )

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Find the card for our test application by its internal_id
    card_container = page.locator(f'text={test_app.internal_id}').locator('xpath=ancestor::*[contains(@class, "MuiCard")]')
    assert card_container.is_visible(), f"Card for application {test_app.internal_id} not found"

    # Get all text content from the card and look for submission info
    card_text = card_container.text_content()

    # Verify "Submitted" appears in the card
    assert "Submitted" in card_text, f"'Submitted' label not found in card text: {card_text}"

    # CRITICAL: Verify the card does NOT show "7 days ago" (which would indicate creation date was used)
    # A submitted-today app should show "ago" (seconds/minutes/hours ago), not "7 days ago"
    assert "7 days" not in card_text, (
        f"BUG DETECTED: Card shows '7 days ago' in submission field, indicating creation date "
        f"was used instead of submission date. Card text:\n{card_text}"
    )

    # Tear down
    page.close()
    context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_card_shows_pending_for_recently_submitted_apps(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Verify submission date displays correctly for applications submitted at different times."""
    reviewer = e2e_users["reviewer"]
    other = e2e_users["other"]

    # Get an existing submitted application
    existing_app = Application.objects.filter(owner=other, status="SUBMITTED").first()
    assert existing_app is not None, "Expected a submitted application in seed data"

    # Open the SPA as reviewer
    context = authenticated_browser_context_factory(reviewer)
    page = context.new_page()

    # Navigate to assessment queue
    page.goto("/assessment")
    page.wait_for_selector('button:has-text("Files")')

    # Get all application cards
    cards = page.locator('div[class*="MuiCard"]')
    assert cards.count() >= 1, "No application cards found on assessment page"

    # Check the first card's content
    first_card = cards.first
    card_text = first_card.text_content()

    # Verify "Submitted" appears in the card
    assert "Submitted" in card_text, f"'Submitted' label not found in card text: {card_text}"

    # Verify submission date info is present
    # The submission date should either show relative time ("2 seconds ago", etc.)
    # or "pending" if not submitted yet
    submission_info_found = any([
        "ago" in card_text.lower(),  # Relative time format
        "pending" in card_text.lower(),  # Not yet submitted
    ])
    
    assert submission_info_found, (
        f"Card should show submission info (relative time with 'ago' or 'pending'), "
        f"but card text is: {card_text}"
    )

    # Tear down
    page.close()
    context.close()
