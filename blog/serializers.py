from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BlogPost

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['public_id', 'name', 'username']


class BlogPostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tag_list = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'public_id', 'title', 'slug', 'content', 'excerpt',
            'author', 'category', 'tags', 'tag_list', 'is_published',
            'published_at', 'featured_image', 'created', 'updated'
        ]
        read_only_fields = ['public_id', 'created', 'updated']
    
    def get_tag_list(self, obj):
        return obj.tag_list