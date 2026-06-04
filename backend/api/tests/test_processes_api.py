"""API tests for authorisation process list/retrieve endpoints."""

import pytest
from rest_framework import status


pytestmark = [pytest.mark.api]


@pytest.mark.django_db
@pytest.mark.security
def test_processes_list_requires_authentication(api_client):
    """Require authentication for process listing so anonymous users cannot inspect metadata."""
    response = api_client.get("/api/processes")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_processes_list_marks_can_review_false_for_non_assessor(
    api_client,
    user,
    process_factory,
):
    """Expose can_review=False for authenticated users with no assessor-group membership."""
    process_factory(slug="proc-a", sort_order=1)
    process_factory(slug="proc-b", sort_order=2)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/processes")

    assert response.status_code == status.HTTP_200_OK
    assert all(item["can_review"] is False for item in response.data)


@pytest.mark.django_db
@pytest.mark.security
def test_processes_list_marks_can_review_true_for_matching_assessor_group(
    api_client,
    assessor_user,
    assessor_group,
    process_factory,
):
    """Mark only linked processes as reviewable for assessor users."""
    reviewable = process_factory(slug="proc-reviewable", sort_order=1)
    not_reviewable = process_factory(slug="proc-non-reviewable", sort_order=2)
    reviewable.assessor_groups.add(assessor_group)

    api_client.force_authenticate(user=assessor_user)
    response = api_client.get("/api/processes")

    assert response.status_code == status.HTTP_200_OK
    by_slug = {item["slug"]: item["can_review"] for item in response.data}
    assert by_slug[reviewable.slug] is True
    assert by_slug[not_reviewable.slug] is False


@pytest.mark.django_db
def test_processes_retrieve_by_slug_returns_exact_record(api_client, user, process_factory):
    """Retrieve process records by slug because slug is the stable API identity."""
    target = process_factory(slug="target-proc", name="Target process")

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/processes/{target.slug}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["slug"] == target.slug
    assert response.data["name"] == "Target process"


@pytest.mark.django_db
def test_processes_retrieve_unknown_slug_returns_404(api_client, user):
    """Return 404 when process slug does not exist so callers cannot infer phantom records."""
    api_client.force_authenticate(user=user)
    response = api_client.get("/api/processes/missing-proc")

    assert response.status_code == status.HTTP_404_NOT_FOUND
