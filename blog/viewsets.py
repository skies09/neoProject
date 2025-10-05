from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import BlogPost
from .serializers import BlogPostSerializer


class BlogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Simple read-only viewset for blog posts
    """
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostSerializer
    lookup_field = 'public_id'
    pagination_class = BlogPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'content', 'excerpt', 'author__name']
    ordering_fields = ['created', 'updated', 'published_at']
    ordering = ['-published_at', '-created']
    filterset_fields = ['category', 'author']
    permission_classes = [permissions.AllowAny]  # Public read access