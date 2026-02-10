import re
from os import path

# Because we are stuck with python 3.12 on Ubuntu 22.04
# The newer guess_file_type is not available to us yet
# TODO: Explicitly use `guess_file_type` once we upgrade
try:
    from mimetypes import guess_file_type
except ImportError:
    from mimetypes import guess_type as guess_file_type

from api.serialisers import JsonSchemaSerialiserMixin
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import filesizeformat
from pyfsig import find_matches_for_file_header
from questionnaires.models import Questionnaire
from rest_framework import exceptions, serializers, status

from .models import Application, ApplicationAttachment, ApplicationStatus
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


# Compile the question index pattern (zero-indexed); examples:
# 0.1-1 : step 0, section 1, question 1
# 2.3-4 : step 2, section 3, question 4
QUESTION_IDX_PATTERN = re.compile(r"^\d+\.\d+\-\d+$")


class AttachmentSerialiser(serializers.ModelSerializer):
    """
    Serializer for ApplicationAttachment model.
    """

    application_key = serializers.UUIDField(
        source="application.key",
        required=False,
        read_only=True,
    )

    download_url = serializers.SerializerMethodField(
        required=False,
        read_only=True,
        method_name="get_download_url",
    )

    class Meta:
        model = ApplicationAttachment
        fields = (
            "key",
            "application_key",
            "question",
            "name",
            "file",
            "created_at",
            "download_url",
        )
        read_only_fields = (
            "key",
            "application_key",
            "question",
            "created_at",
            "download_url",
        )
        # `file` field is write-only and required only when creating a new attachment.
        extra_kwargs = {
            "file": {"write_only": True},
        }

    def get_download_url(self, obj: ApplicationAttachment) -> str | None:
        request = self.context.get("request")
        if request is None:
            return None

        return obj.get_download_url(request)

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        request = self.context.get("request", None)
        isPost = request.method == "POST"
        # isPut = request.method == "PUT"
        isPatch = request.method == "PATCH"

        # `application` field is required only when first creating
        fields["application_key"].required = isPost
        fields["application_key"].read_only = not isPost

        # `question` field is required only when first creating
        fields["question"].required = isPost
        fields["question"].read_only = not isPost

        # `file` field is writable / required only when first creating the instance
        fields["file"].required = isPost
        fields["file"].read_only = not isPost

        # `name` field is writable only on first create or PATCH updates, but not on PUT updates
        fields["name"].required = isPost or isPatch
        fields["name"].read_only = not (isPost or isPatch)

        return fields

    def validate_file(self, value: serializers.FileField) -> serializers.FileField:
        """
        Validate the uploaded file for size and type, using both the file header and extension.
        """
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

        # Reset the file pointer to the beginning after reading the header
        value.seek(0)

        for match in matches:
            match_mimetype, _ = guess_file_type(f"file.{match.file_extension}")
            # File extension must match and mime type must be allowed
            if (
                match.file_extension == extension
                and match_mimetype in settings.UPLOAD_MIME_TYPES
            ):
                return value

        # Decline by default
        raise exceptions.ValidationError(
            "File type cannot be determined or is not allowed."
        )

    def validate_application_key(self, value):
        """
        Validate the application key to ensure it exists and belongs to the user.
        Also, cache the application instance in the context for later use in create().
        """
        request = self.context.get("request")
        try:
            application = Application.objects.get(key=value, owner=request.user)
        except Application.DoesNotExist:
            raise serializers.ValidationError(
                {"application_key": "Application not found."}
            )

        # Cache for later to avoid re-query in create()
        self.context["application"] = application
        return value

    def validate_question(self, value):
        """
        Validate the question index to ensure it follows the expected format.

        Looking up the actual question type being a "file" in the questionnaire
        is possible, however is an overkill for the time being.
        """
        question_idx = value.strip()
        if not question_idx:
            raise serializers.ValidationError(
                {"question": "Question index cannot be empty."}
            )

        # Perform a regex check to ensure the format
        if not re.match(QUESTION_IDX_PATTERN, question_idx):
            raise serializers.ValidationError(
                {"question": "Question index does not match the expected format. "}
            )

        return question_idx

    def create(self, validated_data):
        # Pull cached instance instead of querying again
        application = self.context.pop("application", None)

        # Explcitly raise an error if we don't have the application instance in the context
        if application is None:
            raise exceptions.ValidationError(
                {
                    "application_key": "Application not found in context, validation did not run."
                }
            )

        # Prepare the attachment instance data
        try:
            data = {
                "application": application,
                "question": validated_data["question"],
                "name": validated_data["name"],
                "file": validated_data["file"],
            }
        except KeyError as e:
            raise serializers.ValidationError("Missing required field: " + str(e))

        # Create the attachment record in an atomic transaction to ensure data integrity
        with transaction.atomic():
            attachment = ApplicationAttachment.objects.create(**data)

        return attachment

    def update(self, instance, validated_data):
        # Disallow changing the file via update endpoints
        if "file" in validated_data:
            raise serializers.ValidationError({"file": "File cannot be updated."})

        # Only allow renaming
        try:
            name = validated_data["name"]
        except KeyError:
            raise serializers.ValidationError({"name": "Name is required for update."})

        # Do update the name and save
        instance.name = name
        instance.save(update_fields=["name"])
        return instance
