from django.contrib import admin
from .models import Kennel

# Register your models here.
@admin.register(Kennel)
class KennelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)