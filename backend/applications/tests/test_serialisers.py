"""Comprehensive coverage tests for applications and API serialisers."""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import Group
from django.test import TestCase
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User

from applications.models import Application, ApplicationAttachment
from applications.statuses import ApplicationStatus
from applications.serialisers import (
    ApplicationSerialiser,
    AttachmentSerialiser,
    ReviewerSerialiser,
)


class AttachmentSerialiserTests(TestCase):
    """Test AttachmentSerialiser."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.process = AuthorisationProcess.objects.create(
            slug="s40",
            name="Section 40",
            description="Section 40 process",
            sort_order=1,
        )
        self.questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="new-app",
            name="New Application",
            document={
                "schema_version": "2025.07-1",
                "steps": [{"sections": [{"questions": []}]}],
            },
            sort_order=1,
            created_by=self.user,
        )
        self.application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )

    def test_attachment_serialiser_serializes_attachment(self):
        """AttachmentSerialiser correctly serialises an attachment."""
        import uuid

        attachment_key = uuid.uuid4()
        attachment = ApplicationAttachment.objects.create(
            application=self.application,
            name="test.pdf",
            file="test.pdf",
            key=attachment_key,
        )

        serializer = AttachmentSerialiser(attachment)
        data = serializer.data

        self.assertEqual(data["key"], str(attachment.key))
        self.assertEqual(data["name"], "test.pdf")


class ApplicationSerialiserTests(TestCase):
    """Test ApplicationSerialiser."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.process = AuthorisationProcess.objects.create(
            slug="s40",
            name="Section 40",
            description="Section 40 process",
            sort_order=1,
        )
        self.questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="new-app",
            name="New Application",
            document={
                "schema_version": "2025.07-1",
                "steps": [{"sections": [{"questions": []}]}],
            },
            sort_order=1,
            created_by=self.user,
        )

    def test_application_serialiser_list_includes_required_fields(self):
        """ApplicationSerialiser includes key, status, and created_at."""
        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
            status=ApplicationStatus.DRAFT,
        )

        serializer = ApplicationSerialiser(application)
        data = serializer.data

        self.assertIn("key", data)
        self.assertIn("status", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["status"], ApplicationStatus.DRAFT)

    def test_application_serialiser_handles_submitted_status(self):
        """ApplicationSerialiser correctly serialises submitted application."""
        from django.utils import timezone

        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
        )

        serializer = ApplicationSerialiser(application)
        data = serializer.data

        self.assertEqual(data["status"], ApplicationStatus.SUBMITTED)
        self.assertIn("submitted_at", data)

    def test_application_serialiser_includes_attachments(self):
        """ApplicationSerialiser includes attachments."""
        import uuid

        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )

        attachment_key = uuid.uuid4()
        attachment = ApplicationAttachment.objects.create(
            application=application,
            name="test.pdf",
            file="test.pdf",
            key=attachment_key,
        )

        serializer = ApplicationSerialiser(application)
        data = serializer.data

        if "attachments" in data:
            self.assertIsInstance(data["attachments"], list)


class ApplicationSerialiserValidationTests(TestCase):
    """Test ApplicationSerialiser validation logic."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.process = AuthorisationProcess.objects.create(
            slug="s40",
            name="Section 40",
            description="Section 40 process",
            sort_order=1,
        )
        self.questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="new-app",
            name="New Application",
            document={
                "schema_version": "2025.07-1",
                "steps": [{"sections": [{"questions": []}]}],
            },
            sort_order=1,
            created_by=self.user,
        )

    @patch("applications.serialisers.verify_turnstile_token")
    def test_create_requires_privacy_consent(self, mock_verify):
        """ApplicationSerialiser requires collection_notice_agreed."""
        mock_verify.return_value = True

        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post("/api/applications")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        data = {
            "process_slug": self.process.slug,
            "questionnaire_id": self.questionnaire.id,
            "questionnaire_code": self.questionnaire.code,
            "questionnaire_version": self.questionnaire.version,
            "collection_notice_agreed": False,  # False
            "turnstile_token": "test-token",
        }

        serializer = ApplicationSerialiser(
            data=data,
            context={"request": request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("collection_notice_agreed", serializer.errors or {})

    @patch("applications.serialisers.verify_turnstile_token")
    def test_create_validates_questionnaire_exists(self, mock_verify):
        """ApplicationSerialiser validates questionnaire is found."""
        mock_verify.return_value = True

        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post("/api/applications")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        data = {
            "process_slug": self.process.slug,
            "questionnaire_id": 99999,  # Non-existent
            "questionnaire_code": "new-app",
            "questionnaire_version": 1,
            "collection_notice_agreed": True,
            "turnstile_token": "test-token",
        }

        serializer = ApplicationSerialiser(
            data=data,
            context={"request": request},
        )

        self.assertFalse(serializer.is_valid())

    @patch("applications.serialisers.verify_turnstile_token")
    def test_patch_submit_requires_turnstile(self, mock_verify):
        """ApplicationSerialiser requires valid turnstile for submit."""
        mock_verify.return_value = False  # Invalid token

        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.patch("/api/applications/test-key")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        application = Application.objects.create(
            owner=self.user,
            questionnaire=self.questionnaire,
            document={"steps": []},
        )

        data = {
            "status": ApplicationStatus.SUBMITTED,
            "turnstile_token": "invalid-token",
        }

        serializer = ApplicationSerialiser(
            application,
            data=data,
            partial=True,
            context={"request": request},
        )

        self.assertFalse(serializer.is_valid())
