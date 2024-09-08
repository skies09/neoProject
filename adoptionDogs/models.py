from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

SIZES = (
    ('XS', 'x-small'), ('S', 'small'), ('M', 'medium'), ('L', 'large'), ('XL', 'x-large')
)

GENDERS = (
    ('Male', 'Male'), ('Female', 'Female')
)

class AdoptionDog(models.Model):
    dog_id = models.CharField(max_length=32 primary_key=True) #PK
    name = models.CharField(max_length=32)
    gender = models.CharField(max_length=16, choices=GENDERS)
    age = models.IntegerField(validators=[MaxValueValidator(30), MinValueValidator(1)])
    size = models.CharField(max_length=16, choices=SIZES)
    weight = models.IntegerField(validators=[MaxValueValidator(100), MinValueValidator(1)])
    good_with_dogs = models.BooleanField()
    good_with_cats = models.BooleanField()
    good_with_children = models.BooleanField()
    breed = models.CharField(max_length=32)
    is_crossbreed = models.BooleanField()
    # kennel_id = models.ForeignKey(Kennels, on_delete=models.CASCADE, to_field='kennel_id')
    # image = models.ImageField(upload_to="adoptionDogs")
    # extra_information = models.CharField(max_length=512)
    # created_at = models.DateTimeField(auto_now_add=True)
    

class Meta:
    ordering = ('-dog_id',)
    verbose_name = 'adoptionDog'
    verbose_name_plural = "adoptionDogs"

def __str__(self):
    return self.name