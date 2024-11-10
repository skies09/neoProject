from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("Old password is not correct.")
        return value

    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise ValidationError("New password cannot be the same as old password.")
        return attrs

    def create(self, validated_data):
        # This method can be used to change the password
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        user.save()
        return user
