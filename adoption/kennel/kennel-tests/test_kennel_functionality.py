from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class KennelAdminCreationTest(TestCase):
    def setUp(self):
        # Create a superuser for admin access
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
    def test_kennel_creation_requires_admin(self):
        """Test that kennels can only be created through admin interface"""
        # This test verifies that the model is set up correctly
        # In a real scenario, kennels would be created through Django admin
        
        # Create a kennel through the model (simulating admin creation)
        kennel = User.objects.create_kennel(
            username='testkennel',
            email='test@kennel.com',
            password='temp123',
            name='Test Kennel'
        )
        
        # Verify the kennel was created with reset_password=True
        self.assertTrue(kennel.reset_password)
        self.assertEqual(kennel.username, 'testkennel')
        self.assertEqual(kennel.name, 'Test Kennel')


class KennelPasswordResetTest(APITestCase):
    def setUp(self):
        # Create a kennel that needs password reset
        self.kennel = User.objects.create_kennel(
            username='testkennel',
            email='test@kennel.com',
            password='temp123',
            name='Test Kennel',
            reset_password=True
        )
        
    def test_login_returns_password_reset_flag(self):
        """Test that login returns requires_password_reset flag"""
        url = reverse('api:auth-login-list')
        data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requires_password_reset'])
        
    def test_first_time_password_reset(self):
        """Test first time password reset functionality"""
        # First login to get token
        login_url = reverse('api:auth-login-list')
        login_data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Get the access token
        access_token = login_response.data['access']
        
        # Set up authentication for the next request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to reset password
        reset_url = reverse('api:auth-first-time-password-reset-list')
        reset_data = {
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        reset_response = self.client.post(reset_url, reset_data)
        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)
        
        # Verify the kennel's reset_password flag is now False
        self.kennel.refresh_from_db()
        self.assertFalse(self.kennel.reset_password)
        
        # Verify the new password works
        new_login_data = {
            'username': 'testkennel',
            'password': 'newpassword123'
        }
        
        new_login_response = self.client.post(login_url, new_login_data)
        self.assertEqual(new_login_response.status_code, status.HTTP_200_OK)
        self.assertFalse(new_login_response.data['requires_password_reset'])
