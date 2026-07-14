"""API tests for assessor queue list/retrieve/update endpoints."""

import pytest
from rest_framework import status

from applications.models import ApplicationStatus


pytestmark = [pytest.mark.api]


@pytest.mark.django_db
@pytest.mark.security
def test_assessment_list_requires_authentication(api_client):
    """Require authentication for assessment queue access."""
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.security
def test_assessment_list_is_empty_for_non_assessor_user(
    api_client,
    user,
    application_factory,
):
    """Return an empty queue for users without assessor-group permissions."""
    application_factory(status=ApplicationStatus.SUBMITTED)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_assessment_list_includes_only_review_queue_statuses(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Expose only statuses configured as review queue entries for assessor workflows."""
    reviewable_process = process_factory(slug="assessable", sort_order=1)
    reviewable_process.assessor_groups.add(assessor_group)
    questionnaire = questionnaire_factory(process=reviewable_process)

    in_queue = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )
    application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.DRAFT,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(in_queue.key)


@pytest.mark.django_db
@pytest.mark.security
def test_assessment_list_includes_only_processes_user_can_review(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Restrict assessment queue rows to processes linked to assessor groups."""
    reviewable_process = process_factory(slug="can-review", sort_order=1)
    reviewable_process.assessor_groups.add(assessor_group)
    non_reviewable_process = process_factory(slug="cannot-review", sort_order=2)

    reviewable_application = application_factory(
        questionnaire=questionnaire_factory(process=reviewable_process),
        status=ApplicationStatus.SUBMITTED,
    )
    application_factory(
        questionnaire=questionnaire_factory(process=non_reviewable_process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(reviewable_application.key)


@pytest.mark.django_db
@pytest.mark.security
def test_assessment_retrieve_returns_404_for_non_assessor(
    api_client,
    user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Hide assessment records from applicants even if they know the application key."""
    process = process_factory(slug="assess-only")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_assessment_retrieve_returns_200_for_assessor_with_process_access(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Return queue item details when the assessor can review the process and status is in queue."""
    process = process_factory(slug="assess-retrieve")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["key"] == str(application.key)


@pytest.mark.django_db
def test_assessment_retrieve_returns_404_for_unreviewable_process(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Hide queue items that belong to processes outside the assessor's group permissions."""
    reviewable_process = process_factory(slug="assess-reviewable")
    reviewable_process.assessor_groups.add(assessor_group)
    foreign_process = process_factory(slug="assess-foreign")
    application = application_factory(
        questionnaire=questionnaire_factory(process=foreign_process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_assessment_patch_allows_reviewer_settable_status(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Allow assessors to move queue items to permitted reviewer statuses."""
    process = process_factory(slug="review-process")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.patch(
        f"/api/assessment/{application.key}",
        {"status": ApplicationStatus.UNDER_REVIEW},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == ApplicationStatus.UNDER_REVIEW


@pytest.mark.django_db
def test_assessment_patch_rejects_non_reviewer_settable_target_status(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Reject assessor attempts to set applicant-only statuses."""
    process = process_factory(slug="review-process")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.patch(
        f"/api/assessment/{application.key}",
        {"status": ApplicationStatus.DRAFT},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be set by an assessor" in str(response.data)


@pytest.mark.django_db
def test_assessment_patch_non_queue_application_returns_404(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Exclude non-queue applications from assessor mutation scope via queryset filtering."""
    process = process_factory(slug="review-process")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.DRAFT,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.patch(
        f"/api/assessment/{application.key}",
        {"status": ApplicationStatus.UNDER_REVIEW},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_assessment_patch_non_status_fields_are_not_persisted(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Ignore non-status payload fields so this endpoint remains status-only for assessors."""
    process = process_factory(slug="review-process")
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )
    original_document = application.document

    api_client.force_authenticate(user=assessor_user)
    response = api_client.patch(
        f"/api/assessment/{application.key}",
        {
            "status": ApplicationStatus.UNDER_REVIEW,
            "document": {
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": True, "answers": {"0-0": "tampered"}}],
            },
        },
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == ApplicationStatus.UNDER_REVIEW
    assert application.document == original_document


@pytest.mark.django_db
def test_assessment_list_includes_owner_email_and_fullname(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify that assessment list responses include owner_email and owner_fullname fields."""
    applicant_user = application_factory(
        questionnaire=questionnaire_factory(
            process=process_factory(slug="test-process", sort_order=1)
        ),
        status=ApplicationStatus.SUBMITTED,
    ).owner
    applicant_user.first_name = "Alice"
    applicant_user.last_name = "Wonder"
    applicant_user.save()
    
    process = process_factory(slug="assessment-process", sort_order=2)
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    data = response.data[0]
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == "Alice Wonder"


@pytest.mark.django_db
def test_assessment_retrieve_includes_owner_email_and_fullname(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify that assessment retrieve responses include owner_email and owner_fullname fields."""
    applicant_user = application_factory(
        questionnaire=questionnaire_factory(
            process=process_factory(slug="test-process-2", sort_order=3)
        ),
        status=ApplicationStatus.SUBMITTED,
    ).owner
    applicant_user.first_name = "Bob"
    applicant_user.last_name = "Builder"
    applicant_user.save()
    
    process = process_factory(slug="retrieve-process", sort_order=4)
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == "Bob Builder"


@pytest.mark.django_db
def test_assessment_owner_fullname_falls_back_to_username_when_empty(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Fallback to username when first_name and last_name are both empty in assessment."""
    applicant_user = application_factory(
        questionnaire=questionnaire_factory(
            process=process_factory(slug="test-process-3", sort_order=5)
        ),
        status=ApplicationStatus.SUBMITTED,
    ).owner
    applicant_user.first_name = ""
    applicant_user.last_name = ""
    applicant_user.save()
    
    process = process_factory(slug="fallback-process", sort_order=6)
    process.assessor_groups.add(assessor_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == applicant_user.username


@pytest.mark.django_db
def test_assessment_response_includes_questionnaire_sort_order(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify questionnaire_sort_order and process_sort_order fields are included in assessment response for sorting."""
    process = process_factory(slug="sort-test", sort_order=1)
    process.assessor_groups.add(assessor_group)
    questionnaire = questionnaire_factory(process=process, sort_order=5)
    application = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get(f"/api/assessment/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    assert "questionnaire_sort_order" in response.data
    assert response.data["questionnaire_sort_order"] == 5
    assert "process_sort_order" in response.data
    assert response.data["process_sort_order"] == 1


@pytest.mark.django_db
def test_assessment_list_includes_questionnaire_sort_order(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify questionnaire_sort_order and process_sort_order are included in assessment list response."""
    process = process_factory(slug="list-sort-test", sort_order=1)
    process.assessor_groups.add(assessor_group)
    questionnaire = questionnaire_factory(process=process, sort_order=3)
    application = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get("/api/assessment")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "questionnaire_sort_order" in response.data[0]
    assert response.data[0]["questionnaire_sort_order"] == 3
    assert "process_sort_order" in response.data[0]
    assert response.data[0]["process_sort_order"] == 1
