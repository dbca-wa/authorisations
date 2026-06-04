from rest_framework import serializers

from .models import AuthorisationProcess


class AuthorisationProcessSerialiser(serializers.ModelSerializer):
    """Serializer for the AuthorisationProcess model."""

    can_review = serializers.BooleanField(read_only=True)

    class Meta:
        model = AuthorisationProcess
        fields = (
            "slug",
            "name",
            "description",
            "sort_order",
            "can_review",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
