from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

# from django.contrib.postgres.fields import ArrayField

SIZES = (
    ("XS", "x-small"),
    ("S", "small"),
    ("M", "medium"),
    ("L", "large"),
    ("XL", "x-large"),
)

GROUPS = (
    ("Gundog", "Gundog"),
    ("Hound", "Hound"),
    ("Pastoral", "Pastoral"),
    ("Terrier", "Terrier"),
    ("Toy", "Toy"),
    ("Utility", "Utility"),
    ("Working", "Working"),
    ("Crossbreed", "Crossbreed"),
    ("Pure", "Pure"),
)


class Breed(models.Model):
    breed = models.CharField(max_length=64)
    group = models.CharField(max_length=16, choices=GROUPS)
    size = models.CharField(null=True, blank=True, max_length=5, choices=SIZES)
    lifespan = models.CharField(null=True, blank=True, max_length=24)
    height = models.CharField(null=True, blank=True, max_length=24)
    weight = models.CharField(null=True, blank=True, max_length=24)
    friendliness = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    family_friendly = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    child_friendly = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    pet_friendly = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    stranger_friendly = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    easy_to_groom = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    energy_levels = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    health = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    shedding_amount = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    barks_howls = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    easy_to_train = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    guard_dog = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    playfulness = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    apartment_dog = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    can_be_alone = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    good_for_busy_owners = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    good_for_new_owners = models.IntegerField(
        null=True, blank=True, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    health_concerns = models.TextField(
        null=True,
        blank=True,
        help_text="Comma-separated list of health concerns"
    )
    short_description = models.TextField(null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    portrait_image = models.ImageField(null=True, blank=True, upload_to="dogs")
    landscape_image = models.ImageField(null=True, blank=True, upload_to="dogs")


# class Meta:
#     ordering = ('-group',)
#     verbose_name = 'breed'
#     verbose_name_plural = "breeds"


def __str__(self):
    return f"{self.breed}"
