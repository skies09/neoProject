import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from adoption.abstract.models import AbstractModel, AbstractManager

SIZES = (
    ('XS', 'x-small'), ('S', 'small'), ('M', 'medium'), ('L', 'large'), ('XL', 'x-large')
)

GENDERS = (
    ('Male', 'Male'), ('Female', 'Female')
)

class DogManager(AbstractManager):
    pass


class Dog(AbstractModel):
    # dog_id = models.UUIDField(db_index=True, unique=True, default=uuid.uuid4, editable=False)
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
    image = models.ImageField(null=True, blank=True, upload_to="adoption/dog/images") 
    kennel = models.ForeignKey(to="adoption_kennel.Kennel", on_delete=models.CASCADE)
    
    objects = DogManager()

    def __str__(self):
        return f"{self.kennel.name}"