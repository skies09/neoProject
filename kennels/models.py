import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Kennel(models.Model):
    kennel_id = models.UUIDField(db_index=True, unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=256, null=True)
    contact_number = models.CharField(max_length=15, null=True)
    email = models.EmailField(max_length=64, null=True, blank=True,)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Kennels"
