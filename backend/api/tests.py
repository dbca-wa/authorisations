import pytest
from rest_framework import status

from applications.models import Application


pytestmark = [pytest.mark.api]


@pytest.mark.django_db
@pytest.mark.security
def test_application_list_is_scoped_to_the_authenticated_owner(
	api_client,
	user,
	other_user,
	questionnaire,
):
	"""Ensure the applications endpoint never exposes another applicant's records."""
	# Create one record for each applicant so the queryset filter has a clear boundary.
	own_application = Application.objects.create(
		owner=user,
		questionnaire=questionnaire,
		document={
			"schema_version": "2025.07-1",
			"active_step": 0,
			"steps": [{"is_valid": None, "answers": {}}],
		},
	)
	Application.objects.create(
		owner=other_user,
		questionnaire=questionnaire,
		document={
			"schema_version": "2025.07-1",
			"active_step": 0,
			"steps": [{"is_valid": None, "answers": {}}],
		},
	)

	api_client.force_authenticate(user=user)
	response = api_client.get("/api/applications")

	assert response.status_code == status.HTTP_200_OK
	assert len(response.data) == 1
	assert response.data[0]["key"] == str(own_application.key)


@pytest.mark.django_db
@pytest.mark.security
def test_attachment_filter_rejects_invalid_application_uuid(api_client, user):
	"""Reject malformed attachment filters so callers cannot probe the endpoint with invalid IDs."""
	api_client.force_authenticate(user=user)

	response = api_client.get("/api/attachments", {"application_key": "not-a-uuid"})

	assert response.status_code == status.HTTP_400_BAD_REQUEST
	assert "badly formed hexadecimal UUID string" in str(response.data)
