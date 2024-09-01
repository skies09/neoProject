from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import ArrayField

SIZES = (
    ('XS', 'x-small'), ('S', 'small'), ('M', 'medium'), ('L', 'large'), ('XL', 'x-large')
)

GROUPS = (
    ('Gundog', 'Gundog'), ('Hound', 'Hound'), ('Pastoral', 'Pastoral'), ('Terrier', 'Terrier'), ('Toy', 'Toy'), ('Utility', 'Utility'), ('Working', 'Working'), ('Crossbreed', 'Crossbreed'), ('Pure', 'Pure')
)

class Breed(models.Model):
    breed = models.CharField(max_length=32) #PK
    group = models.CharField(max_length=16, choices=GROUPS)
    size = models.CharField(max_length=5, choices=SIZES)
    # lifespan = models.CharField(max_length=8)
    # height = models.CharField(max_length=8)
    # weight = models.CharField(max_length=8)
    # friendliness = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # family_friendly = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # child_friendly = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # pet_friendly = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # stranger_friendly = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # easy_to_groom = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # energy_levels = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # health = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # shedding_amount = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # barks_howls = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # easy_to_train = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # guard_dog = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # playfulness = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # apartment_dog = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # can_be_alone = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # good_for_busy_owners = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # good_for_new_owners = models.IntegerField(validators=[MaxValueValidator(10), MinValueValidator(1)])
    # health_concerns = ArrayField(models.CharField(max_length=200), blank=True)
    # short_description = models.CharField(max_length=256)
    # long_description = models.CharField(max_length=528)
    # portrait_image = models.ImageField(upload_to="dogs")
    # landscape_image = models.ImageField(upload_to="dogs")

    

class Meta:
    ordering = ('-group',)
    verbose_name = 'breed'
    verbose_name_plural = "breeds"

def __str__(self):
    return self.breed