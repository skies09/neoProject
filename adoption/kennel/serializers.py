from rest_framework import serializers
from adoption.kennel.models import Kennel
from adoption.abstract.serializers import AbstractSerializer
from rest_framework.exceptions import ValidationError


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


class KennelPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """Validate that the old password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise ValidationError("Old password is not correct.")
        return value

    def validate(self, attrs):
        """Validate that new password and confirm password match, and new password is different from old."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise ValidationError("New password and confirm password do not match.")
        
        if attrs["old_password"] == attrs["new_password"]:
            raise ValidationError("New password cannot be the same as old password.")
        
        return attrs

    def create(self, validated_data):
        """Change the kennel user's password."""
        user = self.context["request"].user
        # Store the current reset_password value
        current_reset_password = user.reset_password
        user.set_password(validated_data["new_password"])
        # Ensure reset_password field remains unchanged
        user.reset_password = current_reset_password
        user.save()
        return user
