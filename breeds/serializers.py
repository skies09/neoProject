from rest_framework import serializers
from breeds.models import Breeds

class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breeds
        fields = ['group', 'breed', 'size']  # Explicitly list the fields you want to include
