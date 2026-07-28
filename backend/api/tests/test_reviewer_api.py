"""API tests for reviewer queue list/retrieve/update endpoints."""

import pytest
from applications.models import ApplicationStatus
from rest_framework import status

pytestmark = [pytest.mark.api]


@pytest.mark.django_db
@pytest.mark.security
def test_reviewer_list_requires_authentication(api_client):
    """Require authentication for reviewer queue access."""
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.security
def test_reviewer_list_is_empty_for_non_reviewer_user(
    api_client,
    user,
    application_factory,
):
    """Return an empty queue for users without reviewer-group permissions."""
    application_factory(status=ApplicationStatus.SUBMITTED)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_reviewer_list_includes_only_review_queue_statuses(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Expose only statuses configured as review queue entries for reviewer workflows."""
    reviewable_process = process_factory(slug="reviewable", sort_order=1)
    reviewable_process.reviewer_groups.add(reviewer_group)
    questionnaire = questionnaire_factory(process=reviewable_process)

    in_queue = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )
    application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.DRAFT,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(in_queue.key)


@pytest.mark.django_db
@pytest.mark.security
def test_reviewer_list_includes_only_processes_user_can_review(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Restrict reviewer queue rows to processes linked to reviewer groups."""
    reviewable_process = process_factory(slug="can-review", sort_order=1)
    reviewable_process.reviewer_groups.add(reviewer_group)
    non_reviewable_process = process_factory(slug="cannot-review", sort_order=2)

    reviewable_application = application_factory(
        questionnaire=questionnaire_factory(process=reviewable_process),
        status=ApplicationStatus.SUBMITTED,
    )
    application_factory(
        questionnaire=questionnaire_factory(process=non_reviewable_process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["key"] == str(reviewable_application.key)


@pytest.mark.django_db
@pytest.mark.security
def test_reviewer_retrieve_returns_404_for_non_reviewer(
    api_client,
    user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Hide reviewer records from applicants even if they know the application key."""
    process = process_factory(slug="review-only")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_reviewer_retrieve_returns_200_for_reviewer_with_process_access(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Return queue item details when the reviewer can review the process and status is in queue."""
    process = process_factory(slug="review-retrieve")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["key"] == str(application.key)


@pytest.mark.django_db
def test_reviewer_retrieve_returns_404_for_unreviewable_process(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Hide queue items that belong to processes outside the reviewer's group permissions."""
    reviewable_process = process_factory(slug="review-reviewable")
    reviewable_process.reviewer_groups.add(reviewer_group)
    foreign_process = process_factory(slug="review-foreign")
    application = application_factory(
        questionnaire=questionnaire_factory(process=foreign_process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_reviewer_patch_allows_reviewer_settable_status(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Allow reviewers to move queue items to permitted reviewer statuses."""
    process = process_factory(slug="review-process")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.patch(
        f"/api/review/{application.key}",
        {"status": ApplicationStatus.UNDER_REVIEW},
        format="json",
    )

    application.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == ApplicationStatus.UNDER_REVIEW


@pytest.mark.django_db
def test_reviewer_patch_rejects_non_reviewer_settable_target_status(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify reviewers can return an application to DRAFT via correct workflow."""
    process = process_factory(slug="review-process")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    
    # First: Transition SUBMITTED → UNDER_REVIEW
    response = api_client.patch(
        f"/api/review/{application.key}",
        {"status": ApplicationStatus.UNDER_REVIEW},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    application.refresh_from_db()
    assert application.status == ApplicationStatus.UNDER_REVIEW
    
    # Then: Transition UNDER_REVIEW → DRAFT
    response = api_client.patch(
        f"/api/review/{application.key}",
        {"status": ApplicationStatus.DRAFT},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    application.refresh_from_db()
    assert application.status == ApplicationStatus.DRAFT


@pytest.mark.django_db
def test_reviewer_patch_restricted_status_returns_400(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Reject reviewer attempts to set restricted statuses like DISCARDED."""
    process = process_factory(slug="review-process")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.patch(
        f"/api/review/{application.key}",
        {"status": ApplicationStatus.DISCARDED},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Error should indicate transition not allowed from SUBMITTED
    assert "Cannot transition from SUBMITTED to DISCARDED" in str(response.data)


@pytest.mark.django_db
def test_reviewer_patch_non_queue_application_returns_404(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Exclude non-queue applications from reviewer mutation scope via queryset filtering."""
    process = process_factory(slug="review-process")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.DRAFT,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.patch(
        f"/api/review/{application.key}",
        {"status": ApplicationStatus.UNDER_REVIEW},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_reviewer_patch_non_status_fields_are_not_persisted(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Ignore non-status payload fields so this endpoint remains status-only for reviewers."""
    process = process_factory(slug="review-process")
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )
    original_document = application.document

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.patch(
        f"/api/review/{application.key}",
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
def test_reviewer_list_includes_owner_email_and_fullname(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify that reviewer list responses include owner_email and owner_fullname fields."""
    applicant_user = application_factory(
        questionnaire=questionnaire_factory(
            process=process_factory(slug="test-process", sort_order=1)
        ),
        status=ApplicationStatus.SUBMITTED,
    ).owner
    applicant_user.first_name = "Alice"
    applicant_user.last_name = "Wonder"
    applicant_user.save()
    
    process = process_factory(slug="review-process", sort_order=2)
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    data = response.data[0]
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == "Alice Wonder"


@pytest.mark.django_db
def test_reviewer_retrieve_includes_owner_email_and_fullname(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify that reviewer retrieve responses include owner_email and owner_fullname fields."""
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
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == "Bob Builder"


@pytest.mark.django_db
def test_reviewer_owner_fullname_falls_back_to_username_when_empty(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Fallback to username when first_name and last_name are both empty in reviewer view."""
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
    process.reviewer_groups.add(reviewer_group)
    application = application_factory(
        owner=applicant_user,
        questionnaire=questionnaire_factory(process=process),
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["owner_email"] == applicant_user.username
    assert data["owner_fullname"] == applicant_user.username


@pytest.mark.django_db
def test_reviewer_response_includes_questionnaire_sort_order(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify questionnaire_sort_order and process_sort_order fields are included in reviewer response for sorting."""
    process = process_factory(slug="sort-test", sort_order=1)
    process.reviewer_groups.add(reviewer_group)
    questionnaire = questionnaire_factory(process=process, sort_order=5)
    application = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get(f"/api/review/{application.key}")

    assert response.status_code == status.HTTP_200_OK
    assert "questionnaire_sort_order" in response.data
    assert response.data["questionnaire_sort_order"] == 5
    assert "process_sort_order" in response.data
    assert response.data["process_sort_order"] == 1


@pytest.mark.django_db
def test_reviewer_list_includes_questionnaire_sort_order(
    api_client,
    reviewer_user,
    reviewer_group,
    process_factory,
    questionnaire_factory,
    application_factory,
):
    """Verify questionnaire_sort_order and process_sort_order are included in reviewer list response."""
    process = process_factory(slug="list-sort-test", sort_order=1)
    process.reviewer_groups.add(reviewer_group)
    questionnaire = questionnaire_factory(process=process, sort_order=3)
    application = application_factory(
        questionnaire=questionnaire,
        status=ApplicationStatus.SUBMITTED,
    )

    api_client.force_authenticate(user=reviewer_user)
    response = api_client.get("/api/review")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert "questionnaire_sort_order" in response.data[0]
    assert response.data[0]["questionnaire_sort_order"] == 3
    assert "process_sort_order" in response.data[0]
    assert response.data[0]["process_sort_order"] == 1
