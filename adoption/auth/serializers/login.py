from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from rest_framework import serializers

from adoption.kennel.serializers import KennelSerializer


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)
        data["user"] = KennelSerializer(self.user, context=self.context).data
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        
        # Check if user needs to reset password
        data["requires_password_reset"] = getattr(self.user, 'reset_password', False)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data