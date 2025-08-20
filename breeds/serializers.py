from rest_framework import serializers
from .models import Breed

class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = [
            'breed', 'group', 'size', 'lifespan', 'height', 'weight',
            'friendliness', 'family_friendly', 'child_friendly', 'pet_friendly',
            'stranger_friendly', 'easy_to_groom', 'energy_levels', 'health',
            'shedding_amount', 'barks_howls', 'easy_to_train', 'guard_dog',
            'playfulness', 'apartment_dog', 'can_be_alone', 'good_for_busy_owners',
            'good_for_new_owners', 'health_concerns', 'short_description',
            'long_description', 'portrait_image', 'landscape_image'
        ]