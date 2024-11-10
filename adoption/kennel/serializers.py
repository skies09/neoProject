from rest_framework import serializers
from adoption.kennel.models import Kennel
from adoption.abstract.serializers import AbstractSerializer

class KennelSerializer(AbstractSerializer):
    class Meta:
        model = Kennel
        fields = [
            'id', 'username', 'name', 'email', 
            'address_line_1', 'town', 'city', 'postcode', 
            'contact_number', 'is_active', 'created', 'updated'
        ]
        read_only_field = ['id', 'is_active', 'created', 'updated']
