from rest_framework import serializers
from .models import Breed, SIZES

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


class BreedMatchRequestSerializer(serializers.Serializer):
    """Serializer for breed matching preferences"""
    size = serializers.ChoiceField(choices=SIZES, required=False, allow_null=True)
    pet_friendly = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    apartment_dog = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    easy_to_groom = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    family_friendly = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    child_friendly = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    energy_levels = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    easy_to_train = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    can_be_alone = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    good_for_busy_owners = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    good_for_new_owners = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    shedding_amount = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    barks_howls = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    playfulness = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    friendliness = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    stranger_friendly = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    guard_dog = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    health = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)


class BreedMatchResponseSerializer(serializers.Serializer):
    """Serializer for breed match response with match rate"""
    breed = BreedSerializer()
    match_rate = serializers.FloatField()