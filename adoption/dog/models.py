from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from adoption.abstract.models import AbstractModel, AbstractManager

SIZES = (
    ("XS", "x-small"),
    ("S", "small"),
    ("M", "medium"),
    ("L", "large"),
    ("XL", "x-large"),
)

GENDERS = (("Male", "Male"), ("Female", "Female"))


class DogManager(AbstractManager):
    pass


class Dog(AbstractModel):
    name = models.CharField(max_length=32, help_text="Dog's name")
    gender = models.CharField(
        max_length=16, choices=GENDERS, null=True, blank=True, help_text="Dog's gender"
    )
    age = models.IntegerField(
        validators=[MaxValueValidator(30), MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Age in years (0-30)",
    )
    size = models.CharField(
        max_length=16,
        choices=SIZES,
        null=True,
        blank=True,
        help_text="Dog's size category",
    )
    weight = models.IntegerField(
        validators=[MaxValueValidator(200), MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Weight in kg (1-200)",
    )
    good_with_dogs = models.BooleanField(
        null=True, blank=True, help_text="Whether the dog gets along with other dogs"
    )
    good_with_cats = models.BooleanField(
        null=True, blank=True, help_text="Whether the dog gets along with cats"
    )
    good_with_children = models.BooleanField(
        null=True, blank=True, help_text="Whether the dog is good with children"
    )
    breed = models.CharField(
        max_length=32, null=True, blank=True, help_text="Dog's breed"
    )
    is_crossbreed = models.BooleanField(
        null=True, blank=True, help_text="Whether the dog is a crossbreed"
    )
    extra_information = models.TextField(
        null=True, blank=True, help_text="Additional information about the dog"
    )
    image = models.ImageField(
        null=True, blank=True, upload_to="adoption/dog/images", help_text="Dog's photo"
    )
    image2 = models.ImageField(
        null=True, blank=True, upload_to="adoption/dog/images", help_text="Dog's second photo"
    )
    image3 = models.ImageField(
        null=True, blank=True, upload_to="adoption/dog/images", help_text="Dog's third photo"
    )
    kennel = models.ForeignKey(
        to="adoption_kennel.Kennel",
        on_delete=models.CASCADE,
        help_text="Kennel that owns this dog",
    )

    objects = DogManager()

    def __str__(self):
        return f"{self.name} ({self.kennel.name})"

    class Meta:
        verbose_name = "Dog"
        verbose_name_plural = "Dogs"
        ordering = ["-created"]
