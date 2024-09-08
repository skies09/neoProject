from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Kennel(models.Model):
    kennel_id = models.CharField(max_length=32, primary_key=True) #PK
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=256)
    contact_number = models.IntegerField()

class Meta:
    ordering = ('-kennel_id',)
    verbose_name = 'kennel'
    verbose_name_plural = "kennels"

def __str__(self):
    return self.name