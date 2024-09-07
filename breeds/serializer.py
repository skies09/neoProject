from rest_framework import serializers
from .models import *

class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        # fields = ['group', 'breed', 'size']
        fields = '__all__'