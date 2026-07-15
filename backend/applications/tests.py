from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase
from django.utils import timezone
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.admin import ApplicationAdmin
from applications.models import Application, ApplicationStatus
from applications.serialisers import ApplicationSerialiser, AttachmentSerialiser


class ApplicationSerialiserTurnstileTests(TestCase):
    """Verify application creation is gated by Turnstile validation."""

    def setUp(self):
        """Create the minimal process, questionnaire, and user needed for creation tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="applicant", password="testpass123"
        )
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

    def _build_patch_request(self):
        """Build a PATCH request with an authenticated owner and client IP."""
        request = self.factory.patch("/api/applications/test-key")
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

    @patch("applications.serialisers.verify_turnstile_token", return_value=True)
    def test_patch_submit_accepts_valid_turnstile_token(
        self, verify_turnstile_token_mock
    ):
        """Allow draft->submitted transition when Turnstile verification succeeds."""
        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        serializer = ApplicationSerialiser(
            instance=application,
            data={
                "status": ApplicationStatus.SUBMITTED,
                "turnstile_token": "patch-token",
            },
            partial=True,
            context={"request": self._build_patch_request()},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.status, ApplicationStatus.SUBMITTED)
        verify_turnstile_token_mock.assert_called_once_with(
            "patch-token",
            "127.0.0.1",
            str(application.key),
        )

    @patch("applications.serialisers.verify_turnstile_token", return_value=False)
    def test_patch_submit_rejects_invalid_turnstile_token(
        self, verify_turnstile_token_mock
    ):
        """Reject draft->submitted transition when Turnstile verification fails."""
        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        serializer = ApplicationSerialiser(
            instance=application,
            data={
                "status": ApplicationStatus.SUBMITTED,
                "turnstile_token": "bad-token",
            },
            partial=True,
            context={"request": self._build_patch_request()},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"turnstile_token": ["Turnstile verification failed. Please try again."]},
        )
        verify_turnstile_token_mock.assert_called_once_with(
            "bad-token",
            "127.0.0.1",
            str(application.key),
        )


class AttachmentSerialiserNameValidationTests(TestCase):
    """Verify attachment name validation, trimming, and empty-check."""

    def setUp(self):
        """Create the minimal objects needed for attachment tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="applicant", password="testpass123"
        )
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
        self.application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

    def _build_patch_request(self):
        """Build a PATCH request with an authenticated owner."""
        request = self.factory.patch(f"/api/attachments/{self.application.key}")
        request.user = self.user
        return request

    def test_validate_name_trims_whitespace(self):
        """Verify that name validation trims leading and trailing whitespace."""
        serializer = AttachmentSerialiser()
        result = serializer.validate_name("  test-file.pdf  ")
        self.assertEqual(result, "test-file.pdf")

    def test_validate_name_accepts_valid_name(self):
        """Verify that valid names without excess whitespace are accepted."""
        serializer = AttachmentSerialiser()
        result = serializer.validate_name("valid-filename.pdf")
        self.assertEqual(result, "valid-filename.pdf")

    def test_validate_name_rejects_empty_string(self):
        """Verify that empty string names are rejected."""
        serializer = AttachmentSerialiser()
        with self.assertRaises(Exception) as context:
            serializer.validate_name("")
        self.assertIn("cannot be empty", str(context.exception))

    def test_validate_name_rejects_whitespace_only(self):
        """Verify that names containing only whitespace are rejected."""
        serializer = AttachmentSerialiser()
        with self.assertRaises(Exception) as context:
            serializer.validate_name("   \t   ")
        self.assertIn("cannot be empty", str(context.exception))

    def test_validate_name_rejects_none(self):
        """Verify that None values are rejected."""
        serializer = AttachmentSerialiser()
        with self.assertRaises(Exception) as context:
            serializer.validate_name(None)
        self.assertIn("cannot be empty", str(context.exception))


class ApplicationAdminResetToDraftTests(TestCase):
    """Verify reset button on admin detail view for submitted applications."""

    def setUp(self):
        """Create admin, users, process, questionnaire, and applications for testing."""
        self.factory = RequestFactory()
        self.admin_site = AdminSite()
        self.app_admin = ApplicationAdmin(Application, self.admin_site)

        # Create superuser (admin staff)
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

        # Create regular user (applicant)
        self.applicant = User.objects.create_user(
            username="applicant", password="testpass123"
        )

        # Create process and questionnaire
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
            created_by=self.admin_user,
        )

    def _build_admin_request(self, method="get"):
        """Build a request with an authenticated admin user."""
        if method.lower() == "post":
            request = self.factory.post("/admin/applications/application/1/change/")
        else:
            request = self.factory.get("/admin/applications/application/1/change/")
        request.user = self.admin_user
        request.session = {}
        # Add messages framework support
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_reset_button_visible_only_for_submitted_status(self):
        """Verify that reset button is displayed only for SUBMITTED applications."""
        # Create a submitted application
        submitted_app = Application.objects.create(
            owner=self.applicant,
            questionnaire=self.questionnaire,
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        # Create a draft application
        draft_app = Application.objects.create(
            owner=self.applicant,
            questionnaire=self.questionnaire,
            status=ApplicationStatus.DRAFT,
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        # Button should appear for submitted
        button_html = self.app_admin.reset_button(submitted_app)
        self.assertIn("Reset to Draft", button_html)
        self.assertIn("_reset_to_draft", button_html)

        # Button should NOT appear for draft
        button_html = self.app_admin.reset_button(draft_app)
        self.assertEqual(button_html, "")

    def test_reset_button_not_visible_for_other_statuses(self):
        """Verify that reset button is hidden for non-submitted statuses."""
        statuses_without_button = [
            ApplicationStatus.DRAFT,
            ApplicationStatus.DISCARDED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.ACTION_REQUIRED,
            ApplicationStatus.UNDER_ASSESSMENT,
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.DEFERRED,
            ApplicationStatus.REJECTED,
        ]

        for status in statuses_without_button:
            app = Application.objects.create(
                owner=self.applicant,
                questionnaire=self.questionnaire,
                status=status,
                document={
                    "schema_version": "2025.07-1",
                    "active_step": 0,
                    "steps": [{"is_valid": None, "answers": {}}],
                },
            )
            button_html = self.app_admin.reset_button(app)
            self.assertEqual(
                button_html,
                "",
                f"Button should not appear for status {status}",
            )

    def test_reset_button_post_resets_application(self):
        """Verify that POSTing the reset button resets the application."""
        # Create a submitted application
        app = Application.objects.create(
            owner=self.applicant,
            questionnaire=self.questionnaire,
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        original_id = app.id
        original_submitted_at = app.submitted_at
        original_document = app.document

        # Simulate POST with _reset_to_draft button
        request = self._build_admin_request(method="post")
        request.POST = {"_reset_to_draft": ""}

        # Call response_change which handles the reset
        self.app_admin.response_change(request, app)

        # Verify the application was reset
        app.refresh_from_db()
        self.assertEqual(app.id, original_id)
        self.assertEqual(app.status, ApplicationStatus.DRAFT)
        self.assertIsNone(app.submitted_at)
        self.assertEqual(app.document, original_document)
        self.assertIsNotNone(original_submitted_at)

    def test_reset_button_preserves_document_data(self):
        """Verify that document data is preserved during reset."""
        # Create application with document data
        document_data = {
            "schema_version": "2025.07-1",
            "active_step": 0,
            "steps": [{"is_valid": None, "answers": {"0-0": "test_answer"}}],
        }
        app = Application.objects.create(
            owner=self.applicant,
            questionnaire=self.questionnaire,
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
            document=document_data,
        )

        # Simulate POST with _reset_to_draft button
        request = self._build_admin_request(method="post")
        request.POST = {"_reset_to_draft": ""}

        # Call response_change
        self.app_admin.response_change(request, app)

        # Verify document was preserved
        app.refresh_from_db()
        self.assertEqual(app.document, document_data)
        self.assertEqual(app.status, ApplicationStatus.DRAFT)
        self.assertIsNone(app.submitted_at)

    def test_reset_shows_success_message(self):
        """Verify that a success message is shown after reset."""
        # Create a submitted application
        app = Application.objects.create(
            owner=self.applicant,
            questionnaire=self.questionnaire,
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
            document={
                "schema_version": "2025.07-1",
                "active_step": 0,
                "steps": [{"is_valid": None, "answers": {}}],
            },
        )

        # Simulate POST with _reset_to_draft button
        request = self._build_admin_request(method="post")
        request.POST = {"_reset_to_draft": ""}

        # Call response_change
        self.app_admin.response_change(request, app)

        # Verify success message is present
        messages_list = list(get_messages(request))
        self.assertGreater(len(messages_list), 0)
        message_text = " ".join(str(m) for m in messages_list)
        self.assertIn("reset to DRAFT status", message_text)
        self.assertIn(app.internal_id, message_text)
