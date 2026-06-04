"""E2E tests for access boundaries and assessor queue behaviour."""

import json

from applications.models import Application, ApplicationAttachment
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_resume_application_owner_can_access_form_shell(
    authenticated_request_context_factory,
    e2e_users,
):
    """Allow only the owner to open the interactive application URL."""
    draft_key = Application.objects.get(owner=e2e_users["applicant"], status="DRAFT").key
    auth_context = authenticated_request_context_factory(e2e_users["applicant"])
    request_context = auth_context["context"]

    try:
        response = request_context.get(f"/a/{draft_key}")
        status = response.status
        body = response.text()
    finally:
        request_context.dispose()

    assert status == 200
    assert '<div id="root"></div>' in body


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_resume_application_reviewer_gets_not_found(
    authenticated_request_context_factory,
    e2e_users,
):
    """Prevent reviewers from opening applicant edit URLs."""
    draft_key = Application.objects.get(owner=e2e_users["applicant"], status="DRAFT").key
    auth_context = authenticated_request_context_factory(e2e_users["reviewer"])
    request_context = auth_context["context"]

    try:
        response = request_context.get(f"/a/{draft_key}")
        status = response.status
    finally:
        request_context.dispose()

    assert status == 404


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_attachment_download_enforces_application_access(
    authenticated_request_context_factory,
    e2e_users,
):
    """Allow owner download and deny non-owner download for an attachment."""
    draft_application = Application.objects.get(owner=e2e_users["applicant"], status="DRAFT")
    attachment = ApplicationAttachment.objects.create(
        application=draft_application,
        question="0-0",
        name="e2e-note.txt",
        file=SimpleUploadedFile("e2e-note.txt", b"hello-e2e", content_type="text/plain"),
    )

    owner_auth = authenticated_request_context_factory(e2e_users["applicant"])
    owner_context = owner_auth["context"]
    try:
        owner_response = owner_context.get(f"/d/{draft_application.key}/{attachment.key}")
        owner_status = owner_response.status
        owner_body = owner_response.body()
    finally:
        owner_context.dispose()

    non_owner_auth = authenticated_request_context_factory(e2e_users["other"])
    non_owner_context = non_owner_auth["context"]
    try:
        non_owner_response = non_owner_context.get(f"/d/{draft_application.key}/{attachment.key}")
        non_owner_status = non_owner_response.status
    finally:
        non_owner_context.dispose()

    assert owner_status == 200
    assert owner_body == b"hello-e2e"
    assert non_owner_status == 404


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_queue_is_reviewer_scoped(
    authenticated_request_context_factory,
    e2e_users,
):
    """Expose assessment queue items only to authorised reviewers."""
    reviewer_auth = authenticated_request_context_factory(e2e_users["reviewer"])
    reviewer_context = reviewer_auth["context"]
    try:
        reviewer_response = reviewer_context.get("/api/assessment")
        reviewer_status = reviewer_response.status
        reviewer_payload = reviewer_response.json()
    finally:
        reviewer_context.dispose()

    applicant_auth = authenticated_request_context_factory(e2e_users["applicant"])
    applicant_context = applicant_auth["context"]
    try:
        applicant_response = applicant_context.get("/api/assessment")
        applicant_status = applicant_response.status
        applicant_payload = applicant_response.json()
    finally:
        applicant_context.dispose()

    assert reviewer_status == 200
    assert len(reviewer_payload) == 1
    assert reviewer_payload[0]["status"] == "SUBMITTED"
    assert applicant_status == 200
    assert applicant_payload == []


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_assessment_status_transition_updates_through_api(
    authenticated_request_context_factory,
    e2e_users,
):
    """Allow reviewers to advance queued applications via the assessment endpoint."""
    submitted_application = Application.objects.get(owner=e2e_users["other"], status="SUBMITTED")
    reviewer_auth = authenticated_request_context_factory(e2e_users["reviewer"])
    reviewer_context = reviewer_auth["context"]

    try:
        response = reviewer_context.patch(
            f"/api/assessment/{submitted_application.key}",
            data=json.dumps({"status": "UNDER_REVIEW"}),
            headers={
                reviewer_auth["csrf_header"]: reviewer_auth["csrf_token"],
                "Content-Type": "application/json",
            },
        )
        status = response.status
        payload = response.json()
    finally:
        reviewer_context.dispose()

    submitted_application.refresh_from_db()

    assert status == 200
    assert payload["status"] == "UNDER_REVIEW"
    assert submitted_application.status == "UNDER_REVIEW"