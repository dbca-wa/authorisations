from api.serialisers import JsonSchemaSerialiserMixin
from questionnaires.models import Questionnaire
from rest_framework import serializers

from .models import Application
from .schema import get_answers_schema


# class ApplicationSerialiser(serializers.HyperlinkedModelSerializer):
class ApplicationSerialiser(
    JsonSchemaSerialiserMixin, serializers.ModelSerializer
):
    """
    Serializer for the Application model.
    """

    # questionnaire_id = serializers.PrimaryKeyRelatedField(
    #     source="questionnaire.id",
    #     read_only=True,
    # )
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
    document = serializers.JSONField(
        required=False,
        read_only=True,
    )

    class Meta:
        model = Application
        fields = (
            "key",
            "owner",
            # "questionnaire_id",
            "questionnaire_slug",
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

        # Questionnaire slug is required when first creating
        fields["questionnaire_slug"].required = isPost
        fields["questionnaire_slug"].read_only = not isPost

        # Document field is not required and read-only when creating
        fields["document"].required = isPut
        fields["document"].read_only = not isPut

        return fields

    def validate_document(self, value):
        schema = get_answers_schema()
        
        # Validate and return with the JSON schema
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
            raise serializers.ValidationError(
                f"Questionnaire with slug '{value}' does not exist."
            )

        # Add the questionnaire to the context for later use
        self.context["questionnaire"] = questionnaire

        # Intentionally return the original value
        return value

    def validate(self, data):
        # Make sure we have the questionnaire object
        questionnaire: Questionnaire = self.context.get("questionnaire", None)
        if questionnaire is None:
            raise serializers.ValidationError("Questionnaire is required")

        validated_data = super().validate(data)

        # This should override the provided "questionnaire" dict field: {"slug": "aec"}
        validated_data["questionnaire"] = questionnaire

        return validated_data

    def create(self, validated_data):
        """
        Create a new Application instance.
        """
        # Add user to validated data
        validated_data["owner"] = self.context["request"].user

        # Create a fresh document with questionnaire schema version
        validated_data["document"] = {
            "answers": {},  # initially empty answers
            "schema_version": None,  # to be set later
        }

        # Hardcode the schema version from the questionnaire
        try:
            validated_data["document"]["schema_version"] = self.context[
                "questionnaire"
            ].document["schema_version"]
        except KeyError:
            # we are past beyond raising a validation error
            raise LookupError(
                "Selected questionnaire doesn't have a schema version, "
                "this is required to create your application and shouldn't happen. "
                "Please contact Ecoinformatics support."
            )

        return super().create(validated_data)

    # def update(self, instance, validated_data):
    #     instance.email = validated_data.get("email", instance.email)
    #     instance.content = validated_data.get("content", instance.content)
    #     instance.created = validated_data.get("created", instance.created)
    #     instance.save()
    #     return instance

    # def create(self, validated_data):
    #     """
    #     Create a new Application instance.
    #     """
    #     # print(validated_data)
    #     # import pdb; pdb.set_trace()

    #         **validated_data
    #     )
