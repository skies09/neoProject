from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_published', 'featured', 'published_at']
    list_filter = ['is_published', 'featured', 'category', 'author', 'created']
    search_fields = ['title', 'content', 'category', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created', 'updated', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'author')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('is_published', 'featured', 'published_at')
        }),
        ('Media', {
            'fields': ('featured_image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New post
            obj.author = request.user
        super().save_model(request, obj, form, change)