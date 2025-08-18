from rest_framework import serializers
from adoption.kennel.models import Kennel
from adoption.abstract.serializers import AbstractSerializer


class KennelSerializer(AbstractSerializer):
    class Meta:
        model = Kennel
        fields = [
            "id",
            "public_id",
            "username",
            "name",
            "email",
            "address_line_1",
            "address_line_2",
            "town",
            "city",
            "postcode",
            "contact_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "created",
            "updated",
            "reset_password",
        ]
        read_only_fields = [
            "id",
            "public_id",
            "username",
            "is_active",
            "is_staff",
            "is_superuser",
            "created",
            "updated",
            "reset_password",
        ]

    def validate_email(self, value):
        """Validate email is unique."""
        user = self.context["request"].user
        if Kennel.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_name(self, value):
        """Validate name is not empty."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip()
