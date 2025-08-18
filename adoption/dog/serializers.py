from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from adoption.abstract.serializers import AbstractSerializer
from adoption.dog.models import Dog
from adoption.kennel.models import Kennel
from adoption.kennel.serializers import KennelSerializer

class DogSerializer(AbstractSerializer):
    kennel = serializers.SlugRelatedField(
        slug_field="public_id",
        read_only=True
    )

    def validate_name(self, value):
        """Validate dog name is not empty and properly formatted."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()

    def validate_age(self, value):
        """Validate age is within reasonable range."""
        if value is not None:
            if value < 0 or value > 30:
                raise serializers.ValidationError("Age must be between 0 and 30 years")
        return value

    def validate_weight(self, value):
        """Validate weight is within reasonable range."""
        if value is not None:
            if value < 1 or value > 200:
                raise serializers.ValidationError("Weight must be between 1 and 200 kg")
        return value

    def validate(self, data):
        """Validate the entire data set."""
        # Only validate 'good_with' fields on creation, not update
        if self.instance is None:  # This is a creation operation
            # Ensure at least one of the 'good_with' fields is provided
            good_with_fields = ['good_with_dogs', 'good_with_cats', 'good_with_children']
            if not any(data.get(field) is not None for field in good_with_fields):
                raise serializers.ValidationError(
                    "At least one compatibility field (good_with_dogs, good_with_cats, good_with_children) should be provided"
                )
        return data

    def create(self, validated_data):
        # Get the kennel from the context (set by the viewset)
        kennel_public_id = self.context.get('kennel_public_id')
        if kennel_public_id:
            try:
                kennel = Kennel.objects.get(public_id=kennel_public_id)
                validated_data['kennel'] = kennel
            except Kennel.DoesNotExist:
                raise ValidationError("Invalid kennel.")
        
        return super().create(validated_data)

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
        fields = [
            'id', 'public_id', 'name', 'gender', 'age', 'size', 'weight',
            'good_with_dogs', 'good_with_cats', 'good_with_children',
            'breed', 'is_crossbreed', 'extra_information', 'image', 'kennel',
            'created', 'updated'
        ]
