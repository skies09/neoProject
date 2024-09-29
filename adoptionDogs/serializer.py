from rest_framework import serializers
from .models import *

class AdoptionDogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdoptionDog
        fields = '__all__'