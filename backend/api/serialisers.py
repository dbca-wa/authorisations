from rest_framework import serializers
from jsonschema import ValidationError, validate

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
        # Perform validation
        try:
            validate(value, schema)
        except ValidationError as e:
            # Get the exact coordinate from error path
            coor: str = ".".join(str(x) for x in e.absolute_path)
            raise serializers.ValidationError(f"Invalid answers: {e.message} ({coor})")

        # Check the schema version matching with previous value
        if self.instance and self.instance.document:
            previous_schema_version = self.instance.document.get("schema_version")
            if (
                previous_schema_version
                and previous_schema_version != value["schema_version"]
            ):
                raise serializers.ValidationError(
                    f"Schema version mismatch: expected {previous_schema_version}, got {value['schema_version']}"
                )

        # Return the validated value
        return value


class ClientConfigSerialiser(serializers.Serializer):
    """
    Serializer for the ClientConfig model.
    """

    base_url = serializers.CharField(default=ClientConfig.base_url)
    csrf_header = serializers.CharField(default=ClientConfig.csrf_header)
    csrf_token = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        return ClientConfig(**validated_data)

    def update(self, instance, validated_data):
        return ClientConfig(**{**instance.__dict__, **validated_data})
