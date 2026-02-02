from mimetypes import guess_file_type
from os import path

from api.serialisers import JsonSchemaSerialiserMixin
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from pyfsig import find_matches_for_file_header
from questionnaires.models import Questionnaire
from rest_framework import exceptions, serializers, status

from .models import Application, ApplicationStatus, ApplicationAttachment
from .schema import get_answers_schema


class ApplicationSerialiser(JsonSchemaSerialiserMixin, serializers.ModelSerializer):
    """
    Serializer for the Application model.
    """

    owner = serializers.CharField(
        source="owner.username",
        required=False,
        read_only=True,
    )
    questionnaire_slug = serializers.SlugField(
        source="questionnaire.slug",
        required=False,
        read_only=True,
    )
    questionnaire_version = serializers.IntegerField(
        source="questionnaire.version",
        required=False,
        read_only=True,
    )
    questionnaire_name = serializers.CharField(
        source="questionnaire.name",
        required=False,
        read_only=True,
    )
    document = serializers.JSONField(
        required=False,
        read_only=True,
    )

    class Meta:
        model = Application
        fields = (
            "key",
            "owner",
            "questionnaire_slug",
            "questionnaire_version",
            "questionnaire_name",
            "status",
            "created_at",
            "updated_at",
            "submitted_at",
            "document",
        )
        # All fields are read-only by default (see `.get_fields()` method).
        read_only_fields = fields

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request", None)
        isPost = request.method == "POST"
        isPut = request.method == "PUT"
        isPatch = request.method == "PATCH"

        # Questionnaire slug is required when first creating
        fields["questionnaire_slug"].required = isPost
        fields["questionnaire_slug"].read_only = not isPost

        # Document field is required only when updating
        fields["document"].required = isPut
        fields["document"].read_only = not isPut

        # Status field is required only when updating via PATCH
        fields["status"].required = isPatch
        fields["status"].read_only = not isPatch

        return fields

    def validate_status(self, value):
        """
        Validate the status field to ensure only allowed transitions.
        """
        # Draft -> Submitted
        if (
            self.instance.status == ApplicationStatus.DRAFT
            and value == ApplicationStatus.SUBMITTED
        ):
            return value

        raise exceptions.ValidationError(
            f"Invalid status transition from {self.instance.status} to {value}"
        )

    def validate_document(self, value):
        if self.instance.status != ApplicationStatus.DRAFT:
            raise exceptions.ValidationError(
                f"Cannot modify document with status '{self.instance.status}'"
            )

        # Validate and return with the JSON schema
        schema = get_answers_schema()
        return self._validate_document(value, schema)

    def validate_questionnaire_slug(self, value):
        """
        Validate the questionnaire slug to ensure it exists in the database.
        """
        questionnaire: Questionnaire = self.context.get("questionnaire", None)

        # Check if we have been already called and validated the slug before
        if isinstance(questionnaire, Questionnaire) and questionnaire.slug == value:
            # Intentionally return the original value
            return value

        # Try to find with the user provided slug
        try:
            questionnaire = Questionnaire.objects.filter(slug=value).latest("version")
        except Questionnaire.DoesNotExist:
            raise exceptions.ValidationError(
                f"Questionnaire with slug '{value}' does not exist."
            )

        # Add the questionnaire to the context for later use
        self.context["questionnaire"] = questionnaire

        # Intentionally return the original value
        return value

    def create(self, validated_data):
        """
        Create a new Application instance.
        """
        # Add user to validated data
        validated_data["owner"] = self.context["request"].user

        # Make sure we have the questionnaire object
        try:
            validated_data["questionnaire"] = self.context["questionnaire"]
        except KeyError:
            raise exceptions.ValidationError("'questionnaire_slug' is required")

        # Create a fresh document with questionnaire schema version
        validated_data["document"] = {
            "schema_version": None,  # to be set later
            # initially with single step
            "active_step": 0,
            "steps": [{"is_valid": None, "answers": {}}],
        }

        # Hardcode the version from the current schema
        schema = get_answers_schema()
        validated_data["document"]["schema_version"] = schema["properties"][
            "schema_version"
        ]["default"]

        # Validate and return with the JSON schema
        self._validate_document(validated_data["document"], schema)
        return super().create(validated_data)


class FileTooLargeError(exceptions.APIException):
    """
    Custom exception for payloads that are too large.
    """

    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "The file is too large."
    default_code = "file_too_large"


class AttachmentSerialiser(serializers.ModelSerializer):
    """
    Serializer for ApplicationAttachment model.
    """
    
    application_key = serializers.UUIDField(
        source="application.key",
        required=True,
        read_only=False,
    )
    
    # download_url = serializers.SerializerMethodField

    class Meta:
        model = ApplicationAttachment
        fields = (
            "key",
            "application_key",
            "answer",
            "name",
            "created_at",
        )
        read_only_fields = (
            "key",
            "application_key",
            "answer",
            "created_at",
        )

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request", None)
        isPost = request.method == "POST"
        # isPut = request.method == "PUT"
        # isPatch = request.method == "PATCH"

        # `application` field is required only when first creating
        fields["application_key"].required = isPost
        fields["application_key"].read_only = not isPost

        # `answer` field is required only when first creating
        fields["answer"].required = isPost
        fields["answer"].read_only = not isPost

        return fields

    # def validate(self, data):
    #     """Make sure only one attachment per answer exists."""
    #     application = self.context.get("application")
    #     answer = data.get("answer")
    #     if application and answer:
    #         exists = ApplicationAttachment.objects.filter(
    #             application=application,
    #             answer=answer,
    #             deleted=False,
    #         ).exists()
    #         if exists:
    #             raise serializers.ValidationError(
    #                 {"answer": "An attachment for this answer already exists."}
    #             )
    #     return data

    def validate_file(self, value: serializers.FileField) -> serializers.FileField:
        # Validate the file size first
        if value.size > settings.UPLOAD_MAX_SIZE:
            raise FileTooLargeError(
                f"File size exceeds the limit of {filesizeformat(settings.UPLOAD_MAX_SIZE)}. "
                f"Current size: {filesizeformat(value.size)}",
            )

        # Get the file extension
        _, extension = path.splitext(value.name)
        extension = extension.lstrip(".").lower()

        # Get the possible mime types based on the "magic bytes"
        matches = find_matches_for_file_header(file_header=value.read(32))
        for match in matches:
            match_mimetype, _ = guess_file_type(f"file.{match.file_extension}")
            # File extension must match and mime type must be allowed
            if (
                match.file_extension == extension
                and match_mimetype in settings.UPLOAD_MIME_TYPES
            ):
                return value

        # Decline by default
        raise exceptions.ValidationError("Unsupported file type.")
