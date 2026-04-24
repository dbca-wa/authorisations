from unittest.mock import patch

from django.test import RequestFactory, TestCase

from applications.serialisers import ApplicationSerialiser
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User


class ApplicationSerialiserTurnstileTests(TestCase):
	"""Verify application creation is gated by Turnstile validation."""

	def setUp(self):
		"""Create the minimal process, questionnaire, and user needed for creation tests."""
		self.factory = RequestFactory()
		self.user = User.objects.create_user(username="applicant", password="testpass123")
		self.process = AuthorisationProcess.objects.create(
			slug="s40",
			name="Section 40",
			description="Section 40 authorisation process",
			sort_order=1,
		)
		self.questionnaire = Questionnaire.objects.create(
			process=self.process,
			code="new-application",
			name="New application",
			description="Create a new application",
			document={
				"schema_version": "2025.07-1",
				"steps": [
					{
						"title": "Step 1",
						"description": "",
						"sections": [
							{
								"title": "Section 1",
								"description": "",
								"questions": [
									{
										"label": "Question 1",
										"type": "text",
										"is_required": False,
										"description": "",
									}
								],
							}
						],
					}
				],
			},
			sort_order=1,
			created_by=self.user,
		)

	def _build_request(self):
		"""Build a POST request with an authenticated owner and client IP."""
		request = self.factory.post("/api/applications")
		request.user = self.user
		request.META["REMOTE_ADDR"] = "127.0.0.1"
		return request

	def _build_payload(self):
		"""Build the minimal valid application creation payload."""
		return {
			"process_slug": self.process.slug,
			"questionnaire_id": self.questionnaire.id,
			"questionnaire_code": self.questionnaire.code,
			"questionnaire_version": self.questionnaire.version,
			"privacy_consent_agreed": True,
			"turnstile_token": "test-token",
		}

	@patch("applications.serialisers.verify_turnstile_token", return_value=True)
	def test_create_accepts_valid_turnstile_token(self, verify_turnstile_token_mock):
		"""Allow application creation when Cloudflare verifies the submitted token."""
		serializer = ApplicationSerialiser(
			data=self._build_payload(),
			context={"request": self._build_request()},
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		application = serializer.save()

		self.assertEqual(application.owner, self.user)
		self.assertEqual(application.questionnaire, self.questionnaire)
		verify_turnstile_token_mock.assert_called_once_with("test-token", "127.0.0.1")

	@patch("applications.serialisers.verify_turnstile_token", return_value=False)
	def test_create_rejects_invalid_turnstile_token(self, verify_turnstile_token_mock):
		"""Reject application creation when Cloudflare verification fails."""
		serializer = ApplicationSerialiser(
			data=self._build_payload(),
			context={"request": self._build_request()},
		)

		self.assertFalse(serializer.is_valid())
		self.assertEqual(
			serializer.errors,
			{"turnstile_token": ["Turnstile verification failed. Please try again."]},
		)
		verify_turnstile_token_mock.assert_called_once_with("test-token", "127.0.0.1")
