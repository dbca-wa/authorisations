"""API tests for questionnaire read endpoints and latest-version behaviour."""

import pytest
from rest_framework import status


pytestmark = [pytest.mark.api]


@pytest.mark.django_db
@pytest.mark.security
def test_questionnaires_list_requires_authentication(api_client):
    """Require authentication for questionnaire listing to avoid exposing form metadata publicly."""
    response = api_client.get("/api/questionnaires")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.integration
def test_questionnaires_list_returns_latest_per_process_and_code(
    api_client,
    user,
    process_factory,
    questionnaire_factory,
):
    """Return only the latest version in each questionnaire lineage for process+code pairs."""
    process = process_factory(slug="s40", sort_order=1)
    old_version = questionnaire_factory(
        process=process,
        code="new",
        version=1,
        sort_order=1,
        name="New v1",
    )
    latest_version = questionnaire_factory(
        process=process,
        code="new",
        version=2,
        sort_order=1,
        name="New v2",
    )
    other_code = questionnaire_factory(
        process=process,
        code="renewal",
        version=3,
        sort_order=2,
        name="Renewal v3",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/questionnaires")

    assert response.status_code == status.HTTP_200_OK
    returned_ids = {item["id"] for item in response.data}
    assert latest_version.id in returned_ids
    assert old_version.id not in returned_ids
    assert other_code.id in returned_ids


@pytest.mark.django_db
def test_questionnaires_list_orders_by_process_then_questionnaire_sort_then_name(
    api_client,
    user,
    process_factory,
    questionnaire_factory,
):
    """Preserve curated display order for process and questionnaire lists in the frontend flow."""
    process_b = process_factory(slug="proc-b", sort_order=2)
    process_a = process_factory(slug="proc-a", sort_order=1)

    q_a2 = questionnaire_factory(
        process=process_a,
        code="a2",
        sort_order=2,
        name="Zeta",
    )
    q_a1 = questionnaire_factory(
        process=process_a,
        code="a1",
        sort_order=1,
        name="Alpha",
    )
    q_b1 = questionnaire_factory(
        process=process_b,
        code="b1",
        sort_order=1,
        name="Beta",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/questionnaires")

    assert response.status_code == status.HTTP_200_OK
    ids_in_order = [item["id"] for item in response.data]
    assert ids_in_order == [q_a1.id, q_a2.id, q_b1.id]


@pytest.mark.django_db
def test_questionnaires_retrieve_by_id_returns_exact_record(
    api_client,
    user,
    process_factory,
    questionnaire_factory,
):
    """Retrieve a specific questionnaire version by concrete ID rather than inferred latest version."""
    process = process_factory(slug="proc-x")
    historical = questionnaire_factory(
        process=process,
        code="new",
        version=1,
        name="Historical",
    )
    questionnaire_factory(
        process=process,
        code="new",
        version=2,
        name="Latest",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get(f"/api/questionnaires/{historical.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == historical.id
    assert response.data["version"] == 1
    assert response.data["name"] == "Historical"


@pytest.mark.django_db
def test_questionnaires_retrieve_unknown_id_returns_404(api_client, user):
    """Return 404 for unknown questionnaire IDs to maintain standard retrieve semantics."""
    api_client.force_authenticate(user=user)
    response = api_client.get("/api/questionnaires/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_questionnaires_list_includes_process_metadata(
    api_client,
    user,
    process_factory,
    questionnaire_factory,
):
    """Verify that questionnaire responses include process slug and name metadata."""
    process = process_factory(slug="s40", name="Section 40")
    questionnaire = questionnaire_factory(
        process=process,
        code="new",
        name="New application",
    )

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/questionnaires")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    data = response.data[0]
    assert data["process_slug"] == "s40"
    assert data["process_name"] == "Section 40"
    assert data["id"] == questionnaire.id
