from rest_framework import serializers
from jsonschema import ValidationError, validate
from django.conf import settings

from api.models import ClientConfig


class JsonSchemaSerialiserMixin(serializers.Serializer):
    """
    A mixer serializer for models with a JSON specification field.
    We cannot simply inherit from an absolute (ABC) class because of Metaclass
    conflicts with rest_framework serializers, therefore using a mixin.
    """

    def _validate_document(self, value, schema):
        """
        Validate the answers field against its schema.
        """
        # Check if the schema version is same as the value's schema version
        expected_version = schema["properties"]["schema_version"]["default"]
        if value["schema_version"] != expected_version:
            raise serializers.ValidationError(
                f"Schema version mismatch: expected {expected_version}, got {value['schema_version']}"
            )

        # Perform validation
        try:
            validate(value, schema)
        except ValidationError as e:
            # Get the exact coordinate from error path
            coor: str = ".".join(str(x) for x in e.absolute_path)
            raise serializers.ValidationError(f"Invalid document: {e.message} ({coor})")

        # Check the schema version matching with previous value
        if self.instance and self.instance.document:
            previous_schema_version = self.instance.document.get("schema_version")
            if (
                previous_schema_version
                and previous_schema_version != value["schema_version"]
            ):
                raise serializers.ValidationError(
                    f"Schema version mismatch: previously {previous_schema_version}, got {value['schema_version']}"
                )

        # Return the validated value
        return value


class ClientConfigSerialiser(serializers.Serializer):
    """
    Serializer for the ClientConfig model.
    """

    api_base = serializers.CharField(default=ClientConfig.api_base)
    csrf_header = serializers.CharField(default=ClientConfig.csrf_header)
    csrf_token = serializers.CharField(required=False, allow_blank=True)
    upload_max_size = serializers.IntegerField(default=ClientConfig.upload_max_size)
    # Provide a fresh copy of the configured mime types as the default so the
    # serializer doesn't reference dataclass Field objects or share a mutable
    # list between instances.
    upload_mime_types = serializers.ListField(
        child=serializers.CharField(), default=list(settings.UPLOAD_MIME_TYPES)
    )

    def create(self, validated_data):
        return ClientConfig(**validated_data)

    def update(self, instance, validated_data):
        return ClientConfig(**{**instance.__dict__, **validated_data})
