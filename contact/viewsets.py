from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .models import Contact
from .serializers import (
    ContactCreateSerializer,
    ContactListSerializer,
    ContactDetailSerializer,
    ContactUpdateSerializer,
    ContactActionSerializer,
    ContactStatsSerializer
)


class ContactFilter(filters.FilterSet):
    """Filter for Contact queryset"""
    
    contact_type = filters.ChoiceFilter(choices=Contact.CONTACT_TYPE_CHOICES)
    priority = filters.ChoiceFilter(choices=Contact.PRIORITY_CHOICES)
    is_actioned = filters.BooleanFilter()
    follow_up_required = filters.BooleanFilter()
    created_after = filters.DateTimeFilter(field_name='created', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created', lookup_expr='lte')
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Contact
        fields = ['contact_type', 'priority', 'is_actioned', 'follow_up_required']
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(contact_number__icontains=value) |
            Q(subject__icontains=value) |
            Q(message__icontains=value)
        )


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contact submissions.
    
    - POST /api/contacts/ - Create new contact (public)
    - GET /api/contacts/ - List contacts (admin only)
    - GET /api/contacts/{id}/ - Get contact details (admin only)
    - PUT/PATCH /api/contacts/{id}/ - Update contact (admin only)
    - DELETE /api/contacts/{id}/ - Delete contact (admin only)
    """
    
    queryset = Contact.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContactFilter
    ordering_fields = ['created', 'priority', 'name', 'email']
    ordering = ['-created', '-priority']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ContactCreateSerializer
        elif self.action == 'list':
            return ContactListSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return ContactDetailSerializer
        return ContactDetailSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]  # Public contact form
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]  # Admin only
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Return queryset with optimizations"""
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.select_related('actioned_by')
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new contact submission.
        This endpoint is public and used by frontend contact forms.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Add request metadata
            contact = serializer.save(
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Return success response
            return Response({
                'message': 'Thank you for your contact. We will get back to you soon!',
                'contact_id': str(contact.public_id),
                'status': 'success'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'Please correct the errors below.',
            'errors': serializer.errors,
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def mark_actioned(self, request, pk=None):
        """Mark a contact as actioned"""
        contact = self.get_object()
        contact.mark_as_actioned(
            user=request.user,
            notes=request.data.get('notes', '')
        )
        return Response({
            'message': 'Contact marked as actioned successfully.',
            'status': 'success'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def mark_follow_up(self, request, pk=None):
        """Mark a contact for follow-up"""
        contact = self.get_object()
        follow_up_date = request.data.get('follow_up_date')
        if follow_up_date:
            follow_up_date = timezone.datetime.fromisoformat(follow_up_date.replace('Z', '+00:00'))
        contact.mark_for_follow_up(follow_up_date)
        return Response({
            'message': 'Contact marked for follow-up successfully.',
            'status': 'success'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_action(self, request):
        """Perform bulk actions on multiple contacts"""
        serializer = ContactActionSerializer(data=request.data)
        if serializer.is_valid():
            contact_ids = request.data.get('contact_ids', [])
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            follow_up_date = serializer.validated_data.get('follow_up_date')
            
            contacts = Contact.objects.filter(public_id__in=contact_ids)
            updated_count = 0
            
            for contact in contacts:
                if action == 'mark_actioned':
                    contact.mark_as_actioned(request.user, notes)
                elif action == 'mark_follow_up':
                    contact.mark_for_follow_up(follow_up_date)
                elif action == 'set_high_priority':
                    contact.priority = 'high'
                elif action == 'set_medium_priority':
                    contact.priority = 'medium'
                elif action == 'set_low_priority':
                    contact.priority = 'low'
                contact.save()
                updated_count += 1
            
            return Response({
                'message': f'{updated_count} contact(s) updated successfully.',
                'status': 'success'
            })
        
        return Response({
            'message': 'Invalid action data.',
            'errors': serializer.errors,
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def stats(self, request):
        """Get contact statistics for admin dashboard"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_contacts = queryset.count()
        pending_contacts = queryset.filter(is_actioned=False).count()
        actioned_contacts = queryset.filter(is_actioned=True).count()
        high_priority_contacts = queryset.filter(priority__in=['high', 'urgent']).count()
        follow_up_required = queryset.filter(follow_up_required=True).count()
        
        # Group by type
        contacts_by_type = dict(queryset.values('contact_type').annotate(
            count=Count('id')
        ).values_list('contact_type', 'count'))
        
        # Group by priority
        contacts_by_priority = dict(queryset.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count'))
        
        # Recent contacts
        recent_contacts = queryset.order_by('-created')[:10]
        recent_serializer = ContactListSerializer(recent_contacts, many=True)
        
        stats_data = {
            'total_contacts': total_contacts,
            'pending_contacts': pending_contacts,
            'actioned_contacts': actioned_contacts,
            'high_priority_contacts': high_priority_contacts,
            'follow_up_required': follow_up_required,
            'contacts_by_type': contacts_by_type,
            'contacts_by_priority': contacts_by_priority,
            'recent_contacts': recent_serializer.data
        }
        
        serializer = ContactStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def pending(self, request):
        """Get all pending (non-actioned) contacts"""
        pending_contacts = self.get_queryset().filter(is_actioned=False)
        serializer = ContactListSerializer(pending_contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def high_priority(self, request):
        """Get all high priority contacts"""
        high_priority_contacts = self.get_queryset().filter(priority__in=['high', 'urgent'])
        serializer = ContactListSerializer(high_priority_contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def follow_up_required(self, request):
        """Get all contacts that require follow-up"""
        follow_up_contacts = self.get_queryset().filter(follow_up_required=True)
        serializer = ContactListSerializer(follow_up_contacts, many=True)
        return Response(serializer.data)
