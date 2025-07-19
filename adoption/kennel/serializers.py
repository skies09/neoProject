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
            "town",
            "city",
            "postcode",
            "contact_number",
            "is_active",
            "created",
            "updated",
            "reset_password",
        ]
        read_only_fields = [
            "id",
            "public_id",
            "is_active",
            "created",
            "updated",
        ]
