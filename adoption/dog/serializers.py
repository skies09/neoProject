from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import os

from adoption.abstract.serializers import AbstractSerializer
from adoption.dog.models import Dog
from adoption.kennel.models import Kennel
from adoption.kennel.serializers import KennelSerializer
from breeds.models import Breed

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

    def validate_image(self, value):
        """Validate uploaded image file."""
        if value is not None:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise serializers.ValidationError("Image file size must be less than 5MB")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = os.path.splitext(value.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Image must be one of the following formats: {', '.join(allowed_extensions)}"
                )
            
            # Check if it's actually an image file
            if not hasattr(value, 'content_type') or not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image")
        
        return value

    def validate_image2(self, value):
        """Validate uploaded image2 file."""
        if value is not None:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise serializers.ValidationError("Image file size must be less than 5MB")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = os.path.splitext(value.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Image must be one of the following formats: {', '.join(allowed_extensions)}"
                )
            
            # Check if it's actually an image file
            if not hasattr(value, 'content_type') or not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image")
        
        return value

    def validate_image3(self, value):
        """Validate uploaded image3 file."""
        if value is not None:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise serializers.ValidationError("Image file size must be less than 5MB")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = os.path.splitext(value.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Image must be one of the following formats: {', '.join(allowed_extensions)}"
                )
            
            # Check if it's actually an image file
            if not hasattr(value, 'content_type') or not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image")
        
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
        
        # Add breed information if breed name exists
        if instance.breed:
            try:
                breed_obj = Breed.objects.filter(breed__iexact=instance.breed).first()
                if breed_obj:
                    rep['breed_info'] = {
                        'breed': breed_obj.breed,
                        'group': breed_obj.group,
                        'size': breed_obj.size,
                        'lifespan': breed_obj.lifespan,
                        'height': breed_obj.height,
                        'weight': breed_obj.weight,
                        'friendliness': breed_obj.friendliness,
                        'family_friendly': breed_obj.family_friendly,
                        'child_friendly': breed_obj.child_friendly,
                        'pet_friendly': breed_obj.pet_friendly,
                        'stranger_friendly': breed_obj.stranger_friendly,
                        'easy_to_groom': breed_obj.easy_to_groom,
                        'energy_levels': breed_obj.energy_levels,
                        'health': breed_obj.health,
                        'shedding_amount': breed_obj.shedding_amount,
                        'barks_howls': breed_obj.barks_howls,
                        'easy_to_train': breed_obj.easy_to_train,
                        'guard_dog': breed_obj.guard_dog,
                        'playfulness': breed_obj.playfulness,
                        'apartment_dog': breed_obj.apartment_dog,
                        'can_be_alone': breed_obj.can_be_alone,
                        'good_for_busy_owners': breed_obj.good_for_busy_owners,
                        'good_for_new_owners': breed_obj.good_for_new_owners,
                        'health_concerns': breed_obj.health_concerns,
                        'short_description': breed_obj.short_description,
                        'long_description': breed_obj.long_description,
                        'portrait_image': breed_obj.portrait_image.url if breed_obj.portrait_image else None,
                        'landscape_image': breed_obj.landscape_image.url if breed_obj.landscape_image else None,
                    }
                else:
                    rep['breed_info'] = None
            except Exception:
                rep['breed_info'] = None
        else:
            rep['breed_info'] = None
        
        return rep

    class Meta:
        model = Dog
        fields = [
            'id', 'public_id', 'name', 'gender', 'age', 'size', 'weight',
            'good_with_dogs', 'good_with_cats', 'good_with_children',
            'breed', 'is_crossbreed', 'extra_information', 'image', 'image2', 'image3', 'kennel',
            'created', 'updated'
        ]


class DogMatchRequestSerializer(serializers.Serializer):
    """Serializer for dog matching preferences. All fields optional. Empty string treated as no preference."""
    gender = serializers.ChoiceField(
        choices=[("Male", "Male"), ("Female", "Female")],
        required=False, allow_null=True, allow_blank=True
    )
    size = serializers.ChoiceField(
        choices=[("XS", "x-small"), ("S", "small"), ("M", "medium"), ("L", "large"), ("XL", "x-large")],
        required=False, allow_null=True, allow_blank=True
    )
    age_min = serializers.IntegerField(min_value=0, max_value=30, required=False, allow_null=True)
    age_max = serializers.IntegerField(min_value=0, max_value=30, required=False, allow_null=True)
    weight_min = serializers.IntegerField(min_value=1, max_value=200, required=False, allow_null=True)
    weight_max = serializers.IntegerField(min_value=1, max_value=200, required=False, allow_null=True)
    good_with_dogs = serializers.BooleanField(required=False, allow_null=True)
    good_with_cats = serializers.BooleanField(required=False, allow_null=True)
    good_with_children = serializers.BooleanField(required=False, allow_null=True)
    breed = serializers.CharField(max_length=32, required=False, allow_null=True, allow_blank=True)
    is_crossbreed = serializers.BooleanField(required=False, allow_null=True)

    def validate_breed(self, value):
        """Breed must be one of the breeds from the breeds API (dropdown selection)."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        stripped = value.strip()
        if not Breed.objects.filter(breed__iexact=stripped).exists():
            raise serializers.ValidationError(
                f"Breed must be selected from the breeds list. No breed found matching '{stripped}'."
            )
        return stripped

    def validate(self, attrs):
        """Normalize empty strings to None so they are treated as 'no preference'."""
        for key in ('gender', 'size', 'breed'):
            if key in attrs and attrs[key] is not None and str(attrs[key]).strip() == '':
                attrs[key] = None
        return attrs


class DogMatchResponseSerializer(serializers.Serializer):
    """Serializer for dog match response with match rate"""
    dog = DogSerializer()
    match_rate = serializers.FloatField()
