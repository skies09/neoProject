import os
import tempfile
from io import StringIO

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .models import Breed

# Register your models here.
@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    change_list_template = "admin/breeds/breed/change_list.html"

    list_display = ('breed', 'group', 'size', 'lifespan', 'height', 'weight', 'display_images')
    list_filter = ('group', 'size')
    search_fields = ('breed', 'group', 'short_description')
    list_per_page = 25
    ordering = ('breed',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('breed', 'group', 'size', 'lifespan', 'height', 'weight')
        }),
        ('Temperament & Behavior', {
            'fields': (
                'friendliness', 'family_friendly', 'child_friendly', 'pet_friendly', 
                'stranger_friendly', 'playfulness', 'guard_dog'
            ),
            'classes': ('collapse',)
        }),
        ('Care & Training', {
            'fields': (
                'easy_to_groom', 'energy_levels', 'easy_to_train', 'shedding_amount', 
                'barks_howls'
            ),
            'classes': ('collapse',)
        }),
        ('Lifestyle Compatibility', {
            'fields': (
                'apartment_dog', 'can_be_alone', 'good_for_busy_owners', 
                'good_for_new_owners', 'health'
            ),
            'classes': ('collapse',)
        }),
        ('Health & Description', {
            'fields': ('health_concerns', 'short_description', 'long_description')
        }),
        ('Images', {
            'fields': ('portrait_image', 'landscape_image'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('breed', 'display_images')  # Make breed read-only since it's the primary identifier
    
    def get_readonly_fields(self, request, obj=None):
        """Make breed field read-only for existing objects"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('breed',)
        return self.readonly_fields
    
    def display_images(self, obj):
        """Display image previews in the list view"""
        images = []
        if obj.portrait_image:
            images.append(f'<img src="{obj.portrait_image.url}" width="30" height="30" style="border-radius: 50%;" title="Portrait" />')
        if obj.landscape_image:
            images.append(f'<img src="{obj.landscape_image.url}" width="30" height="30" style="border-radius: 50%;" title="Landscape" />')
        
        if images:
            return format_html(' '.join(images))
        return "No images"
    
    display_images.short_description = 'Images'
    display_images.allow_tags = True
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related()

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "import-dogdb/",
                self.admin_site.admin_view(self.import_dogdb_view),
                name="breeds_breed_import_dogdb",
            ),
        ] + urls

    def import_dogdb_view(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied

        max_upload_bytes = 8 * 1024 * 1024  # 8 MiB

        if request.method == "POST":
            upload = request.FILES.get("csv_file")
            if not upload:
                messages.error(request, "Choose a CSV file to upload.")
                return redirect("admin:breeds_breed_import_dogdb")
            reported = getattr(upload, "size", None)
            if reported is not None and reported > max_upload_bytes:
                messages.error(
                    request,
                    f"File too large (max {max_upload_bytes // (1024 * 1024)} MB).",
                )
                return redirect("admin:breeds_breed_import_dogdb")

            tmp_path = None
            try:
                fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="dogdb_import_")
                written = 0
                with os.fdopen(fd, "wb") as tmp:
                    for chunk in upload.chunks():
                        written += len(chunk)
                        if written > max_upload_bytes:
                            raise ValueError("_upload_too_large")
                        tmp.write(chunk)

                stdout = StringIO()
                stderr = StringIO()
                try:
                    call_command(
                        "import_dogdb_csv",
                        tmp_path,
                        update=True,
                        stdout=stdout,
                        stderr=stderr,
                    )
                except Exception as exc:
                    messages.error(request, f"Import failed: {exc}")
                else:
                    err = stderr.getvalue().strip()
                    if err:
                        messages.warning(request, err[:2000])
                    messages.success(
                        request,
                        f"Import finished. {Breed.objects.count()} breeds in the database.",
                    )
            except ValueError as exc:
                if str(exc) == "_upload_too_large":
                    messages.error(
                        request,
                        f"File too large (max {max_upload_bytes // (1024 * 1024)} MB).",
                    )
                else:
                    messages.error(request, f"Import failed: {exc}")
            finally:
                if tmp_path and os.path.isfile(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

            return redirect("admin:breeds_breed_changelist")

        return render(
            request,
            "admin/breeds/breed/import_dogdb.html",
            {
                "title": "Import breeds from CSV",
                "opts": self.model._meta,
                "max_mb": max_upload_bytes // (1024 * 1024),
            },
        )

    actions = ['mark_as_complete', 'mark_as_incomplete']
    
    def mark_as_complete(self, request, queryset):
        """Mark selected breeds as having complete information"""
        updated = queryset.update(
            friendliness__isnull=False,
            family_friendly__isnull=False,
            child_friendly__isnull=False,
            pet_friendly__isnull=False,
            stranger_friendly__isnull=False,
            easy_to_groom__isnull=False,
            energy_levels__isnull=False,
            health__isnull=False,
            shedding_amount__isnull=False,
            barks_howls__isnull=False,
            easy_to_train__isnull=False,
            guard_dog__isnull=False,
            playfulness__isnull=False,
            apartment_dog__isnull=False,
            can_be_alone__isnull=False,
            good_for_busy_owners__isnull=False,
            good_for_new_owners__isnull=False
        )
        self.message_user(request, f'{updated} breeds marked as complete.')
    
    mark_as_complete.short_description = "Mark selected breeds as complete"
    
    def mark_as_incomplete(self, request, queryset):
        """Mark selected breeds as having incomplete information"""
        updated = queryset.update(
            friendliness=None,
            family_friendly=None,
            child_friendly=None,
            pet_friendly=None,
            stranger_friendly=None,
            easy_to_groom=None,
            energy_levels=None,
            health=None,
            shedding_amount=None,
            barks_howls=None,
            easy_to_train=None,
            guard_dog=None,
            playfulness=None,
            apartment_dog=None,
            can_be_alone=None,
            good_for_busy_owners=None,
            good_for_new_owners=None
        )
        self.message_user(request, f'{updated} breeds marked as incomplete.')
    
    mark_as_incomplete.short_description = "Mark selected breeds as incomplete"