from django.db import models
from django.core.validators import EmailValidator
from adoption.abstract.models import AbstractModel


class Contact(AbstractModel):
    """
    Contact model for handling contact form submissions and rescue center signups.
    Used for both general contact forms and rescue center registrations.
    """
    
    CONTACT_TYPE_CHOICES = [
        ('general', 'General Contact'),
        ('rescue_signup', 'Rescue Center Signup'),
        ('adoption_inquiry', 'Adoption Inquiry'),
        ('support', 'Support Request'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Required fields
    name = models.CharField(
        max_length=255,
        help_text="Full name of the person contacting"
    )
    email = models.EmailField(
        max_length=255,
        validators=[EmailValidator()],
        help_text="Email address for contact"
    )
    contact_number = models.CharField(
        max_length=20,
        help_text="Phone number for contact"
    )
    
    # Optional address fields
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="First line of address"
    )
    town = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Town or locality"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City"
    )
    postcode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Postal/ZIP code"
    )
    
    # Contact details
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        default='general',
        help_text="Type of contact submission"
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Subject of the contact"
    )
    message = models.TextField(
        help_text="Main message content"
    )
    
    # Status and action fields
    is_actioned = models.BooleanField(
        default=False,
        help_text="Whether this contact has been actioned by admin"
    )
    actioned_by = models.ForeignKey(
        'adoption_kennel.Kennel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actioned_contacts',
        help_text="Admin user who actioned this contact"
    )
    actioned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this contact was actioned"
    )
    action_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about the action taken"
    )
    
    # Priority and organization
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of this contact"
    )
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the submitter"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string from the request"
    )
    
    # Follow-up fields
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether a follow-up is required"
    )
    follow_up_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled follow-up date"
    )
    
    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ['-created', '-priority']
        indexes = [
            models.Index(fields=['contact_type', 'is_actioned']),
            models.Index(fields=['priority', 'created']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.contact_type} ({'Actioned' if self.is_actioned else 'Pending'})"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = []
        if self.address_line_1:
            address_parts.append(self.address_line_1)
        if self.town:
            address_parts.append(self.town)
        if self.city:
            address_parts.append(self.city)
        if self.postcode:
            address_parts.append(self.postcode)
        return ', '.join(address_parts) if address_parts else 'No address provided'
    
    @property
    def is_high_priority(self):
        """Check if this contact is high priority"""
        return self.priority in ['high', 'urgent']
    
    def mark_as_actioned(self, user, notes=None):
        """Mark this contact as actioned by a specific user"""
        from django.utils import timezone
        
        # Only allow staff users to mark contacts as actioned
        if not user.is_staff:
            raise ValueError("Only staff users can mark contacts as actioned")
        
        self.is_actioned = True
        self.actioned_by = user
        self.actioned_at = timezone.now()
        if notes:
            self.action_notes = notes
        self.save()
    
    def mark_for_follow_up(self, follow_up_date=None):
        """Mark this contact for follow-up"""
        self.follow_up_required = True
        if follow_up_date:
            self.follow_up_date = follow_up_date
        self.save()