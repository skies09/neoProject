from rest_framework import serializers

from adoption.kennel.serializers import KennelSerializer
from adoption.kennel.models import Kennel


class RegisterSerializer(KennelSerializer):
    """
    Registration serializer for requests and user creation
    """

    # Making sure the password is at least 8 characters long, and no longer than 128 and can't be read
    # by the user
    password = serializers.CharField(
        max_length=128, min_length=8, write_only=True, required=True
    )

    class Meta:
        model = Kennel
        # List of all the fields that can be included in a request or a response
        fields = [
            "id",
            # "kennel_id",
            "name",
            "email",
            "username",
            "address_line_1", 
            "address_line_2", 
            "town" ,
            "city",
            "postcode",
            "contact_number", 
            "password",
        ]

    def create(self, validated_data):
        # Use the `create_kennel` method we wrote earlier for the UserManager to create a new user.
        return Kennel.objects.create_kennel(**validated_data)