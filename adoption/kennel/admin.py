from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Kennel


@admin.register(Kennel)
class KennelAdmin(UserAdmin):
    list_display = ('username', 'name', 'email', 'is_active', 'is_staff', 'reset_password', 'created')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'reset_password', 'created')
    search_fields = ('username', 'name', 'email')
    ordering = ('-created',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('name', 'email')}),
        (_('Address'), {'fields': ('address_line_1', 'address_line_2', 'town', 'city', 'postcode')}),
        (_('Contact'), {'fields': ('contact_number',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created', 'updated')}),
        (_('Password Reset'), {'fields': ('reset_password',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'email', 'password1', 'password2', 'reset_password'),
        }),
    )
    
    readonly_fields = ('created', 'updated', 'last_login')
    
    def save_model(self, request, obj, form, change):
        # If this is a new kennel (not being edited), ensure reset_password is True
        if not change:
            obj.reset_password = True
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
