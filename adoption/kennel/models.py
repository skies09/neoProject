from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from adoption.abstract.models import AbstractModel

class KennelManager(BaseUserManager):
    def create_kennel(self, username, email, password=None, **kwargs):
        if username is None:
            raise TypeError('Users must have a username.')
        if email is None:
            raise TypeError('Users must have an email.')
        if password is None:
            raise TypeError('Users must have a password.')
        
        kennel = self.model(
            username=username, 
            email=self.normalize_email(email), 
            **kwargs
        )
        kennel.set_password(password)
        kennel.save(using=self._db)
        return kennel
    
    def create_superuser(self, username, email, password, **kwargs):
        if password is None:
            raise TypeError('Superusers must have a password.')
        if email is None:
            raise TypeError('Superusers must have an email.')
        if username is None:
            raise TypeError('Superusers must have a username.')

        kennel = self.create_kennel(username, email, password, **kwargs)
        kennel.is_superuser = True
        kennel.is_staff = True  # Ensuring superusers have admin access
        kennel.save(using=self._db)
        return kennel
    
    def get_object_by_public_id(self, public_id):
        try:
            return self.get(id=public_id)
        except self.model.DoesNotExist:
            return None 

class Kennel(AbstractModel, AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True, unique=True)
    address_line_1 = models.CharField(max_length=128, null=True)
    address_line_2 = models.CharField(max_length=128, null=True, blank=True)
    town = models.CharField(max_length=64, null=True)
    city = models.CharField(max_length=64, null=True)
    postcode = models.CharField(max_length=10, null=True)
    contact_number = models.CharField(max_length=15, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin access
    is_superuser = models.BooleanField(default=False)
    # reset_password = models.BooleanField(default=True) # Reset password on first login

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="kennel_groups",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="kennel_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = KennelManager()

    def __str__(self):
        return f"{self.email}"
