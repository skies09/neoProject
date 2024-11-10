from django.contrib import admin
from .models import Breed

# Register your models here.
@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ('breed', 'group', 'size')
    list_filter = ('breed', 'group', 'size')
    search_fields = ('breed', 'group')