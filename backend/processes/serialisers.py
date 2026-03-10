from rest_framework import serializers

from .models import AuthorisationProcess


class AuthorisationProcessSerialiser(serializers.ModelSerializer):
    """Serializer for the AuthorisationProcess model."""

    class Meta:
        model = AuthorisationProcess
        fields = (
            "slug",
            "name",
            "description",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
