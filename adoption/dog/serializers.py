from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from adoption.abstract.serializers import AbstractSerializer
from adoption.dog.models import Dog
from adoption.kennel.models import Kennel
from adoption.kennel.serializers import KennelSerializer

class DogSerializer(AbstractSerializer):
    kennel = serializers.SlugRelatedField(
        queryset=Kennel.objects.all(), slug_field="public_id"
    )

    def validate_kennel(self, value):
        if self.context["request"].user.username != value.username: 
            raise ValidationError("You can't create a dog for another kennel.")
        return value
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Save the updated Dog instance
        instance.save()  
        return instance
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.kennel:
            rep['kennel'] = KennelSerializer(instance.kennel).data
        else:
            rep['kennel'] = None
        return rep

    class Meta:
        model = Dog
        fields = '__all__'
