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
from django.db import IntegrityError, transaction
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
    process_slug = serializers.SlugField(
        source="questionnaire.process.slug",
        required=False,
        read_only=True,
    )
    questionnaire_id = serializers.IntegerField(
        source="questionnaire.id",
        required=False,
        read_only=True,
    )
    questionnaire_name = serializers.CharField(
        source="questionnaire.name",
        required=False,
        read_only=True,
    )
    questionnaire_version = serializers.IntegerField(
        source="questionnaire.version",
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
            "id",
            "key",
            "owner",
            "process_slug",
            "questionnaire_id",
            "questionnaire_name",
            "questionnaire_version",
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

        # Default to False when request is not present (e.g., during schema generation)
        isPost = request.method == "POST" if request else False
        isPut = request.method == "PUT" if request else False
        isPatch = request.method == "PATCH" if request else False

        # CREATE / POST
        # Questionnaire ID is required when creating
        fields["questionnaire_id"].required = isPost
        fields["questionnaire_id"].read_only = not isPost
        # Process slug is required when creating (to confirm data integrity)
        fields["process_slug"].required = isPost
        fields["process_slug"].read_only = not isPost
        # Questionnaire name is required when creating (to confirm data integrity)
        fields["questionnaire_name"].required = isPost
        fields["questionnaire_name"].read_only = not isPost
        # Questionnaire version is required when creating (to confirm data integrity)
        fields["questionnaire_version"].required = isPost
        fields["questionnaire_version"].read_only = not isPost

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

    def validate(self, attrs):
        """
        Object-level validation to ensure the questionnaire exists and matches the provided process slug, name, and version.
        This runs after field-level validation, guaranteeing access to all fields.
        """
        # Only validate on creation for data integrity
        request = self.context.get("request")
        if request.method != "POST":
            return attrs

        questionnaire_data = attrs.get("questionnaire") or {}
        process_data = questionnaire_data.get("process") or {}

        process_slug = process_data.get("slug")
        questionnaire_id = questionnaire_data.get("id")
        questionnaire_name = questionnaire_data.get("name")
        questionnaire_version = questionnaire_data.get("version")
        
        # Make sure we did receive those required fields
        if (
            not process_slug
            or not questionnaire_id
            or not questionnaire_name
            or not questionnaire_version
        ):
            raise exceptions.ValidationError(
                "Process slug, questionnaire id, name and version are required."
            )

        # If we already have a validated questionnaire in the context, validate it
        questionnaire: Questionnaire = self.context.get("questionnaire", None)
        if (
            isinstance(questionnaire, Questionnaire)
            and questionnaire.process.slug == process_slug
            and questionnaire.id == questionnaire_id
            and questionnaire.name == questionnaire_name
            and questionnaire.version == questionnaire_version
        ):
            return attrs

        # Otherwise, try to find the questionnaire based on the provided fields
        try:
            questionnaire = Questionnaire.objects.select_related("process").get(
                process__slug=process_slug,
                id=questionnaire_id,
                name=questionnaire_name,
                version=questionnaire_version,
            )
        except Questionnaire.DoesNotExist:
            raise exceptions.ValidationError(
                "Questionnaire with the provided process slug, id, name and version does not exist."
            )

        # Add the found questionnaire to the context for later use
        self.context["questionnaire"] = questionnaire

        return attrs

    def create(self, validated_data):
        """
        Create a new Application instance.
        """
        # Make sure we have the questionnaire object
        try:
            questionnaire = self.context["questionnaire"]
        except KeyError:
            raise exceptions.ValidationError("Questionnaire not found in context, validation did not run.")

        # Hardcode the version from the current schema
        schema = get_answers_schema()

        # Create a fresh document with questionnaire schema version
        document = {
            "schema_version": schema["properties"]["schema_version"]["default"],
            # initially with single step
            "active_step": 0,
            "steps": [{"is_valid": None, "answers": {}}],
        }

        # Validate and return with the JSON schema
        self._validate_document(document, schema)

        create_data = {
            "owner": self.context["request"].user,
            "questionnaire": questionnaire,
            "document": document,
        }

        return super().create(create_data)


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

        # Default to False when request is not present (e.g., during schema generation)
        isPost = request.method == "POST" if request else False
        isPatch = request.method == "PATCH" if request else False

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
            application = Application.objects.select_related(
                "questionnaire", "questionnaire__process"
            ).get(key=value, owner=request.user)
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found.")

        # Cache for later to avoid re-query in create()
        self.context["application"] = application
        return value

    def validate_question(self, value):
        """
        Validate the question index format (does not parse definition here).
        Definition parsing is deferred to object-level validate() for guaranteed ordering.
        """
        question_idx = value.strip()
        if not question_idx:
            raise serializers.ValidationError("Question index cannot be empty.")

        # Regex validates format: ensures all digits and correct structure
        if not re.match(QUESTION_IDX_PATTERN, question_idx):
            raise serializers.ValidationError(
                "Question index must follow format: step.section-question (e.g., 0.1-2)"
            )

        return question_idx

    def validate(self, data):
        """
        Object-level validation: Parse question definition and validate against file_max_attachments.
        This runs after all field validators, guaranteeing access to cached application.
        """
        # Get the cached application from field validator
        application = self.context.get("application")
        if application is None:
            raise serializers.ValidationError(
                "Application not found in context. Ensure application_key validation ran first."
            )

        # Parse question index: "step.section-question" format
        # Regex already validated format in validate_question(), so this won't fail
        question_idx = data.get("question", "")
        parts = question_idx.split("-")
        step_section, question_num = parts[0].split("."), int(parts[1])
        step_idx, section_idx = int(step_section[0]), int(step_section[1])

        # Look up the question in questionnaire document
        try:
            question_def = application.questionnaire.document["steps"][step_idx][
                "sections"
            ][section_idx]["questions"][question_num]
        except (KeyError, IndexError, TypeError):
            raise serializers.ValidationError(
                {"question": "Question not found in questionnaire definition."}
            )

        # Cache the question definition for use in create()
        self.context["question_def"] = question_def

        return data

    def create(self, validated_data):
        # Pull cached instances
        application = self.context.pop("application", None)
        question_def = self.context.pop("question_def", None)

        # Explicitly raise errors if we don't have the required cached values
        if application is None:
            raise exceptions.ValidationError(
                {
                    "application_key": "Application not found in context, validation did not run."
                }
            )

        if question_def is None:
            raise exceptions.ValidationError(
                {
                    "question": "Question definition not found in context, validation did not run."
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

        # Validate file_max_attachments limit and create in atomic transaction
        # Use select_for_update() to serialize concurrent requests for the same application
        # and prevent race conditions where multiple requests bypass the attachment limit check
        question_idx = validated_data["question"]
        max_attachments = min(question_def.get("file_max_attachments") or 1, 20)

        with transaction.atomic():
            # Lock the application row to prevent concurrent attachment creation
            Application.objects.select_for_update().get(pk=application.pk)

            # Count existing non-deleted attachments within the transaction
            # This ensures we're counting after acquiring the lock
            existing_count = ApplicationAttachment.objects.filter(
                application=application,
                question=question_idx,
                is_deleted=False,
            ).count()

            # Validate the limit under the lock
            if existing_count >= max_attachments:
                raise serializers.ValidationError(
                    {
                        "file": f"Maximum {max_attachments} attachment(s) allowed for this question, current: {existing_count}"
                    }
                )

            # Create the attachment record (still within atomic + locked transaction)
            try:
                attachment = ApplicationAttachment.objects.create(**data)
            except IntegrityError as e:
                raise serializers.ValidationError(
                    "An attachment for this question already exists. " + str(e)
                )

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
