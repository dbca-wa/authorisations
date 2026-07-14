"""E2E: full end-to-end user flow (create → edit → submit → download).

This test exercises the SPA from the applicant perspective using browser
interactions: starts a new application, completes a simple question,
submits the application, and verifies the generated PDF download is
available to the owner.
"""

from urllib.parse import urlparse
import pytest


@pytest.mark.skip
@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_user_create_edit_submit_and_download(
    authenticated_browser_context_factory,
    authenticated_request_context_factory,
    e2e_users,
    mock_turnstile_script,
):
    applicant = e2e_users["applicant"]

    # Open an authenticated browser context and attach the Turnstile mock
    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    # Start a new application from the New Application page
    page.goto("/new-application")
    page.wait_for_selector('button:has-text("Start Application")')
    start_buttons = page.locator('button:has-text("Start Application")')
    assert start_buttons.count() >= 1
    start_buttons.nth(0).click()

    # If a confirmation dialog appears because an in-progress application
    # exists, accept it to proceed to the privacy consent dialog.
    try:
        # Short timeout because most runs will not hit this branch.
        page.wait_for_selector('button:has-text("Confirm")', timeout=500)
        page.get_by_role("button", name="Confirm").click()
    except Exception:
        # No confirmation dialog shown — continue normally.
        pass

    # Privacy consent dialog: wait for verification to complete and interact
    page.wait_for_selector('role=dialog')
    dialog = page.locator('role=dialog')
    # Locator objects do not implement wait_for_selector; use Locator.wait_for
    dialog.locator('input[type="checkbox"]:not([disabled])').wait_for(state="visible", timeout=5000)
    dialog.locator('input[type="checkbox"]').click()

    # Click "I agree" and capture the newly opened editor tab.
    with context.expect_page() as new_page_info:
        dialog.locator('button:has-text("I agree")').click()
    new_page = new_page_info.value
    # Ensure the editor page is ready and attach Turnstile mock for later
    mock_turnstile_script(new_page)
    new_page.wait_for_selector('div#root')

    # Fill the simple form (seed questionnaires use a single text field)
    # Locate by its label (MUI TextField uses the label as accessible name).
    title_input = new_page.get_by_label("Project title")
    title_input.fill("E2E Project Title")

    # Continue to the review page (this triggers a save)
    new_page.get_by_role("button", name="Continue").click()

    # On the review page, ensure Turnstile is mocked and confirm + submit
    mock_turnstile_script(new_page)
    new_page.wait_for_selector('input[type="checkbox"]:not([disabled])', timeout=5000)
    new_page.locator('input[type="checkbox"]').click()
    new_page.get_by_role("button", name="Submit Application").click()

    # Extract application key from the editor page URL (/a/<key>)
    parsed = urlparse(new_page.url)
    app_key = parsed.path.rstrip("/").split("/")[-1]

    # Close the editor tab and refresh My Applications to observe the submitted item
    new_page.close()
    page.goto("/my-applications")

    # Wait for the download action to appear for the new application
    download_selector = f'a[aria-label="Download application PDF"][href="/d/{app_key}"]'
    page.wait_for_selector(download_selector, timeout=5000)
    download_links = page.locator(download_selector)
    assert download_links.count() == 1

    # Verify the download endpoint returns PDF bytes for the owner
    req_auth = authenticated_request_context_factory(applicant)
    req_ctx = req_auth["context"]
    resp = req_ctx.get(f"/d/{app_key}")
    assert resp.status == 200
    # Our E2E fixture returns deterministic PDF bytes beginning with %PDF
    body = resp.body()
    assert body.startswith(b"%PDF")

    # Clean up
    page.close()
    context.close()
