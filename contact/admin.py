from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'contact_type', 'priority', 'is_actioned', 
        'actioned_by', 'created', 'contact_number_display'
    )
    list_filter = (
        'contact_type', 'priority', 'is_actioned', 'follow_up_required',
        'created', 'actioned_at'
    )
    search_fields = (
        'name', 'email', 'contact_number', 'subject', 'message',
        'address_line_1', 'town', 'city', 'postcode'
    )
    readonly_fields = (
        'public_id', 'created', 'updated', 'actioned_at', 
        'ip_address', 'user_agent', 'full_address_display'
    )
    ordering = ('-created', '-priority')
    
    fieldsets = (
        (_('Contact Information'), {
            'fields': (
                'name', 'email', 'contact_number', 'contact_type', 'priority'
            )
        }),
        (_('Address Information'), {
            'fields': (
                'address_line_1', 'town', 'city', 'postcode', 'full_address_display'
            ),
            'classes': ('collapse',)
        }),
        (_('Message Details'), {
            'fields': ('subject', 'message')
        }),
        (_('Status & Actions'), {
            'fields': (
                'is_actioned', 'actioned_by', 'actioned_at', 'action_notes',
                'follow_up_required', 'follow_up_date'
            ),
            'description': 'Only staff users can assign who actioned this contact.'
        }),
        (_('Technical Information'), {
            'fields': ('public_id', 'ip_address', 'user_agent', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_actioned', 'mark_for_follow_up', 'set_high_priority']
    
    def contact_number_display(self, obj):
        """Display contact number with formatting"""
        if obj.contact_number:
            return format_html(
                '<a href="tel:{}">{}</a>',
                obj.contact_number,
                obj.contact_number
            )
        return '-'
    contact_number_display.short_description = 'Phone Number'
    
    def full_address_display(self, obj):
        """Display formatted full address"""
        address = obj.full_address
        if address != 'No address provided':
            return format_html('<span style="color: #666;">{}</span>', address)
        return format_html('<span style="color: #999; font-style: italic;">{}</span>', address)
    full_address_display.short_description = 'Full Address'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('actioned_by')
    
    def mark_as_actioned(self, request, queryset):
        """Admin action to mark contacts as actioned"""
        updated = queryset.update(
            is_actioned=True,
            actioned_by=request.user,
            actioned_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} contact(s) marked as actioned.',
            level='SUCCESS'
        )
    mark_as_actioned.short_description = "Mark selected contacts as actioned"
    
    def mark_for_follow_up(self, request, queryset):
        """Admin action to mark contacts for follow-up"""
        updated = queryset.update(follow_up_required=True)
        self.message_user(
            request,
            f'{updated} contact(s) marked for follow-up.',
            level='SUCCESS'
        )
    mark_for_follow_up.short_description = "Mark selected contacts for follow-up"
    
    def set_high_priority(self, request, queryset):
        """Admin action to set contacts as high priority"""
        updated = queryset.update(priority='high')
        self.message_user(
            request,
            f'{updated} contact(s) set to high priority.',
            level='SUCCESS'
        )
    set_high_priority.short_description = "Set selected contacts to high priority"
    
    def get_form(self, request, obj=None, **kwargs):
        """Override form to restrict actioned_by field to staff users only"""
        form = super().get_form(request, obj, **kwargs)
        
        # Only allow staff users to edit the actioned_by field
        if not request.user.is_staff:
            if 'actioned_by' in form.base_fields:
                form.base_fields['actioned_by'].disabled = True
                form.base_fields['actioned_by'].help_text = "Only staff users can assign who actioned this contact."
        else:
            # For staff users, limit the queryset to only staff users
            if 'actioned_by' in form.base_fields:
                from adoption.kennel.models import Kennel
                form.base_fields['actioned_by'].queryset = Kennel.objects.filter(is_staff=True)
                form.base_fields['actioned_by'].help_text = "Select a staff member who actioned this contact."
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Override save to handle actioned status and permissions"""
        # Only allow staff users to modify actioned_by field
        if not request.user.is_staff and hasattr(obj, 'actioned_by'):
            # If user is not staff, don't allow them to change actioned_by
            if change:  # Only for existing objects
                # Get the original object to preserve the actioned_by field
                original = Contact.objects.get(pk=obj.pk)
                obj.actioned_by = original.actioned_by
                obj.actioned_at = original.actioned_at
        
        # Auto-assign current user if contact is marked as actioned and no one is assigned
        if obj.is_actioned and not obj.actioned_by and request.user.is_staff:
            obj.actioned_by = request.user
            obj.actioned_at = timezone.now()
        
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Check if user has permission to change the object"""
        return super().has_change_permission(request, obj)
    
    def has_add_permission(self, request):
        """Check if user has permission to add new objects"""
        return super().has_add_permission(request)
    
    def get_list_display(self, request):
        """Customize list display based on user permissions"""
        display = list(super().get_list_display(request))
        if not request.user.is_superuser:
            # Remove sensitive fields for non-superusers
            if 'ip_address' in display:
                display.remove('ip_address')
        return display
    
    class Media:
        css = {
            'all': ('admin/css/contact_admin.css',)
        }
        js = ('admin/js/contact_admin.js',)


# Custom admin site configuration for better UX
admin.site.site_header = "NeoProject Administration"
admin.site.site_title = "NeoProject Admin"
admin.site.index_title = "Welcome to NeoProject Administration"