from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Contact

User = get_user_model()


class ContactCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new contact submissions.
    Used by frontend forms to submit contact requests.
    """
    
    class Meta:
        model = Contact
        fields = [
            'name', 'email', 'contact_number', 'address_line_1', 'town', 
            'city', 'postcode', 'contact_type', 'subject', 'message', 'priority'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'contact_number': {'required': True},
            'message': {'required': True},
            'address_line_1': {'required': False},
            'town': {'required': False},
            'city': {'required': False},
            'postcode': {'required': False},
            'subject': {'required': False},
            'priority': {'required': False},
        }
    
    def validate_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower()
    
    def validate_contact_number(self, value):
        """Validate contact number format"""
        if not value:
            raise serializers.ValidationError("Please provide a contact number.")
        # Remove any non-digit characters for validation
        digits_only = ''.join(filter(str.isdigit, value))
        if len(digits_only) < 7:
            raise serializers.ValidationError("Please provide a valid contact number.")
        return value
    
    def validate_name(self, value):
        """Validate name field"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Please provide a valid name.")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message field"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide a message with at least 10 characters.")
        return value.strip()


class ContactListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing contacts (admin view).
    Includes basic information for list views.
    """
    actioned_by_name = serializers.CharField(source='actioned_by.name', read_only=True)
    full_address = serializers.CharField(read_only=True)
    is_high_priority = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'public_id', 'name', 'email', 'contact_number', 'contact_type',
            'priority', 'is_actioned', 'actioned_by_name', 'actioned_at',
            'created', 'full_address', 'is_high_priority', 'follow_up_required'
        ]


class ContactDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed contact view (admin).
    Includes all fields for detailed admin interface.
    """
    actioned_by_name = serializers.CharField(source='actioned_by.name', read_only=True)
    actioned_by_username = serializers.CharField(source='actioned_by.username', read_only=True)
    full_address = serializers.CharField(read_only=True)
    is_high_priority = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'public_id', 'name', 'email', 'contact_number', 'address_line_1',
            'town', 'city', 'postcode', 'contact_type', 'subject', 'message',
            'priority', 'is_actioned', 'actioned_by', 'actioned_by_name',
            'actioned_by_username', 'actioned_at', 'action_notes',
            'follow_up_required', 'follow_up_date', 'ip_address', 'user_agent',
            'created', 'updated', 'full_address', 'is_high_priority'
        ]
        read_only_fields = [
            'public_id', 'created', 'updated', 'ip_address', 'user_agent',
            'actioned_by_name', 'actioned_by_username', 'full_address', 'is_high_priority'
        ]


class ContactUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating contact records (admin only).
    Allows admins to update status, notes, and other fields.
    """
    
    class Meta:
        model = Contact
        fields = [
            'contact_type', 'priority', 'is_actioned', 'action_notes',
            'follow_up_required', 'follow_up_date'
        ]
    
    def validate_follow_up_date(self, value):
        """Validate follow-up date is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Follow-up date must be in the future.")
        return value


class ContactActionSerializer(serializers.Serializer):
    """
    Serializer for quick contact actions (mark as actioned, etc.).
    """
    action = serializers.ChoiceField(choices=[
        ('mark_actioned', 'Mark as Actioned'),
        ('mark_follow_up', 'Mark for Follow-up'),
        ('set_high_priority', 'Set High Priority'),
        ('set_medium_priority', 'Set Medium Priority'),
        ('set_low_priority', 'Set Low Priority'),
    ])
    notes = serializers.CharField(required=False, allow_blank=True)
    follow_up_date = serializers.DateTimeField(required=False)
    
    def validate_follow_up_date(self, value):
        """Validate follow-up date is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Follow-up date must be in the future.")
        return value


class ContactStatsSerializer(serializers.Serializer):
    """
    Serializer for contact statistics (admin dashboard).
    """
    total_contacts = serializers.IntegerField()
    pending_contacts = serializers.IntegerField()
    actioned_contacts = serializers.IntegerField()
    high_priority_contacts = serializers.IntegerField()
    follow_up_required = serializers.IntegerField()
    contacts_by_type = serializers.DictField()
    contacts_by_priority = serializers.DictField()
    recent_contacts = ContactListSerializer(many=True)
