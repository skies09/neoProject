from django.db import models
from django.contrib.auth import get_user_model
from adoption.abstract.models import AbstractModel

User = get_user_model()


class BlogPost(AbstractModel):
    """
    Simple blog post model
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True, default='')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, blank=True, default='')
    tags = models.CharField(max_length=500, blank=True, default='', help_text="Comma-separated tags")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    featured_image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at', '-created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []