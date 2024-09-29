import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from kennels.models import Kennel
from django.utils import timezone

SIZES = (
    ('XS', 'x-small'), ('S', 'small'), ('M', 'medium'), ('L', 'large'), ('XL', 'x-large')
)

GENDERS = (
    ('Male', 'Male'), ('Female', 'Female')
)

class AdoptionDog(models.Model):
    dog_id = models.UUIDField(db_index=True, unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    gender = models.CharField(max_length=16, choices=GENDERS, null=True)
    age = models.IntegerField(validators=[MaxValueValidator(30), MinValueValidator(1)], null=True)
    size = models.CharField(max_length=16, choices=SIZES, null=True)
    weight = models.IntegerField(validators=[MaxValueValidator(100), MinValueValidator(1)], null=True)
    good_with_dogs = models.BooleanField(null=True)
    good_with_cats = models.BooleanField(null=True)
    good_with_children = models.BooleanField(null=True)
    breed = models.CharField(max_length=32, null=True)
    is_crossbreed = models.BooleanField()
    extra_information = models.TextField(null=True, blank=True)
    # image = models.ImageField(upload_to="adoptionDogs") 
    kennel = models.ForeignKey(
        Kennel,
        on_delete=models.CASCADE,
        related_name='adoption_dogs' 
    )
    created_at = models.DateField(auto_now=True, null=True, blank=True,) 

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Adoption Dogs" 