"""Test API schema version validation for applications."""

import pytest
from rest_framework import exceptions

from applications.models import Application
from applications.schema import SCHEMA_VERSION
from applications.serialisers import ApplicationSerialiser
from applications.statuses import ApplicationStatus
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire
from users.models import User


@pytest.mark.django_db
class TestApplicationsSerializerSchemaValidation:
    """Verify serializer enforces schema version on validate_document."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create an authorisation process
        self.process = AuthorisationProcess.objects.create(
            name="Test Process",
            slug="test-process",
            description="Test Description"
        )
        
        # Create a questionnaire
        self.questionnaire = Questionnaire.objects.create(
            process=self.process,
            code="test_q",
            name="Test Questionnaire",
            version=1,
            document={"schema_version": 1, "steps": []},
            created_by=self.user
        )
    
    def test_validate_document_accepts_correct_schema_version(self):
        """validate_document accepts document with correct schema_version."""
        app = Application.objects.create(
            questionnaire=self.questionnaire,
            owner=self.user,
            document={"schema_version": SCHEMA_VERSION, "active_step": 0, "steps": []},
            status=ApplicationStatus.DRAFT
        )
        
        serializer = ApplicationSerialiser(app)
        document = {
            "schema_version": SCHEMA_VERSION,
            "active_step": 1,
            "steps": [{"is_valid": True, "answers": {}}]
        }
        
        # Should not raise exception
        result = serializer.validate_document(document)
        assert result is not None
    
    def test_validate_document_rejects_wrong_schema_version(self):
        """validate_document rejects document with wrong schema_version."""
        app = Application.objects.create(
            questionnaire=self.questionnaire,
            owner=self.user,
            document={"schema_version": SCHEMA_VERSION, "active_step": 0, "steps": []},
            status=ApplicationStatus.DRAFT
        )
        
        serializer = ApplicationSerialiser(app)
        document = {
            "schema_version": 999,  # Wrong version
            "active_step": 0,
            "steps": [{"is_valid": False, "answers": {}}]
        }
        
        # Should raise ValidationError
        with pytest.raises(exceptions.ValidationError) as exc_info:
            serializer.validate_document(document)
        
        error_text = str(exc_info.value).lower()
        assert "schema_version" in error_text or "999" in error_text
    
    def test_validate_document_rejects_missing_schema_version(self):
        """validate_document rejects document without schema_version."""
        app = Application.objects.create(
            questionnaire=self.questionnaire,
            owner=self.user,
            document={"schema_version": SCHEMA_VERSION, "active_step": 0, "steps": []},
            status=ApplicationStatus.DRAFT
        )
        
        serializer = ApplicationSerialiser(app)
        document = {
            # Missing schema_version
            "active_step": 0,
            "steps": [{"is_valid": False, "answers": {}}]
        }
        
        # Should raise ValidationError
        with pytest.raises(exceptions.ValidationError) as exc_info:
            serializer.validate_document(document)
        
        error_text = str(exc_info.value).lower()
        assert "schema" in error_text and "version" in error_text


