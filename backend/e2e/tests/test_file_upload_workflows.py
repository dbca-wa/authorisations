"""E2E tests for draft editor file-upload user workflows.

These tests exercise real browser interactions for:
- successful uploads,
- invalid upload recovery,
- multi-attachment delete flows,
- required field validation before submission.
"""

from __future__ import annotations

import copy

import pytest
from applications.models import Application, ApplicationAttachment
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from questionnaires.models import Questionnaire


FILE_QUESTION_APPLICATION_KEY = "00000000-0000-4000-8000-000000000003"
FILE_QUESTION_KEY = "0.0-0"


def _get_file_question_application(e2e_users) -> Application:
    """Return the seeded draft application that contains the file question."""
    owner = e2e_users["other"]
    return Application.objects.select_related("questionnaire").get(
        owner=owner,
        key=FILE_QUESTION_APPLICATION_KEY,
        status="DRAFT",
    )


def _reset_attachments(application: Application):
    """Remove existing attachments so each scenario starts from a deterministic state."""
    ApplicationAttachment.objects.filter(application=application).delete()


def _upload_file(page, *, name: str, mime_type: str, content: bytes):
    """Upload a file via the hidden file input in the dropzone."""
    file_input = page.locator('input[type="file"]').first
    file_input.wait_for(state="attached", timeout=5000)
    file_input.set_input_files(
        {
            "name": name,
            "mimeType": mime_type,
            "buffer": content,
        }
    )


def _attachment_link(page, filename: str):
    """Return the attachment tile link for a specific filename."""
    return page.get_by_role("link", name=filename)


def _wait_for_application_patch(page, application_key: str):
    """Wait for the attachment-triggered autosave request, tolerating fast-response races."""
    try:
        page.wait_for_event(
            "response",
            lambda response: (
                response.url.endswith(f"/api/applications/{application_key}")
                and response.request.method in {"PUT", "PATCH"}
            ),
            timeout=15000,
        )
    except PlaywrightTimeoutError:
        # In faster runtimes, the autosave response can complete before this listener attaches.
        page.wait_for_load_state("networkidle", timeout=5000)


def _set_file_question_config(
    questionnaire: Questionnaire,
    *,
    max_attachments: int,
    is_required: bool,
):
    """Update the seeded file question config for deterministic upload scenarios."""
    updated_document = copy.deepcopy(questionnaire.document)
    file_question = updated_document["steps"][0]["sections"][0]["questions"][0]
    file_question["is_required"] = is_required
    file_question["config"] = {
        **(file_question.get("config") or {}),
        "file_max_attachments": max_attachments,
    }
    questionnaire.document = updated_document
    questionnaire.save(update_fields=["document"])


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_upload_flow_supports_multiple_valid_files(
    authenticated_browser_context_factory,
    e2e_users,
):
    """User uploads valid files and receives success feedback for each upload."""
    application = _get_file_question_application(e2e_users)
    _reset_attachments(application)
    _set_file_question_config(application.questionnaire, max_attachments=3, is_required=False)

    context = authenticated_browser_context_factory(e2e_users["other"])
    page = context.new_page()

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        page.get_by_role("button", name="Select from computer").wait_for(timeout=5000)

        _upload_file(
            page,
            name="workflow-one.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.4\nworkflow-one",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)
        assert _attachment_link(page, "workflow-one.pdf").is_visible()

        _upload_file(
            page,
            name="workflow-two.png",
            mime_type="image/png",
            content=b"\x89PNG\r\n\x1a\nworkflow-two",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)
        assert _attachment_link(page, "workflow-two.png").is_visible()

        # The seeded question allows up to 3 files, so upload control remains available after 2 uploads.
        page.get_by_role("button", name="Select from computer").wait_for(state="visible", timeout=7000)
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_invalid_upload_shows_error_and_allows_retry(
    authenticated_browser_context_factory,
    e2e_users,
):
    """User sees an error for invalid files, then successfully retries with a valid file."""
    application = _get_file_question_application(e2e_users)
    _reset_attachments(application)
    _set_file_question_config(application.questionnaire, max_attachments=3, is_required=False)

    context = authenticated_browser_context_factory(e2e_users["other"])
    page = context.new_page()

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        _upload_file(
            page,
            name="invalid.txt",
            mime_type="text/plain",
            content=b"plain-text-is-not-allowed",
        )
        page.get_by_text("Invalid file type, please ensure it meets the requirements.").wait_for(timeout=5000)

        _upload_file(
            page,
            name="retry-success.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.4\nretry-success",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)
        assert _attachment_link(page, "retry-success.pdf").is_visible()
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_multiple_attachment_delete_keeps_upload_available(
    authenticated_browser_context_factory,
    e2e_users,
):
    """User uploads two files, deletes one, and can continue uploading."""
    application = _get_file_question_application(e2e_users)
    _reset_attachments(application)
    _set_file_question_config(application.questionnaire, max_attachments=3, is_required=False)

    context = authenticated_browser_context_factory(e2e_users["other"])
    page = context.new_page()

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        _upload_file(
            page,
            name="delete-me.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.4\ndelete-me",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)

        _upload_file(
            page,
            name="keep-me.png",
            mime_type="image/png",
            content=b"\x89PNG\r\n\x1a\nkeep-me",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)

        assert _attachment_link(page, "delete-me.pdf").is_visible()
        assert _attachment_link(page, "keep-me.png").is_visible()

        page.get_by_title("Delete: delete-me.pdf").click()
        page.get_by_role("button", name="Delete").click()
        page.get_by_text("File has been deleted").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)

        assert _attachment_link(page, "keep-me.png").is_visible()
        assert page.locator("text=delete-me.pdf").count() == 0
        page.get_by_role("button", name="Select from computer").wait_for(state="visible", timeout=7000)
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_editor_required_file_blocks_continue_until_upload(
    authenticated_browser_context_factory,
    e2e_users,
):
    """Required file question blocks progression until a valid file is attached."""
    application = _get_file_question_application(e2e_users)
    _reset_attachments(application)
    _set_file_question_config(application.questionnaire, max_attachments=1, is_required=True)

    context = authenticated_browser_context_factory(e2e_users["other"])
    page = context.new_page()

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)

        page.get_by_role("button", name="Continue").click()
        page.get_by_role("alert").filter(has_text="This field is required.").wait_for(timeout=5000)

        _upload_file(
            page,
            name="required-file.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.4\nrequired-file",
        )
        page.get_by_text("File has been uploaded").wait_for(timeout=5000)
        _wait_for_application_patch(page, application.key)

        page.get_by_role("button", name="Continue").click()
        page.get_by_role("button", name="Submit Application").wait_for(timeout=5000)
    finally:
        page.close()
        context.close()
