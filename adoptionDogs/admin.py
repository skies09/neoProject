from django.contrib import admin
from .models import AdoptionDog

# Register your models here.
@admin.register(AdoptionDog)
class AdoptionDogAdmin(admin.ModelAdmin):
    list_display = ('name', 'breed', 'age')
    list_filter = ('name', 'breed', 'age')
    search_fields = ('name', 'breed', 'age')