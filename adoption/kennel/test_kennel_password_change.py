from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from adoption.kennel.models import Kennel
from adoption.kennel.serializers import KennelPasswordChangeSerializer


class KennelPasswordChangeTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create a test kennel user
        self.kennel = Kennel.objects.create_kennel(
            username='testkennel',
            email='test@kennel.com',
            password='oldpassword123',
            name='Test Kennel'
        )

    def test_kennel_password_change_serializer_validation(self):
        """Test the serializer validation logic."""
        context = {'request': type('MockRequest', (), {'user': self.kennel})()}
        
        # Test valid data
        valid_data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = KennelPasswordChangeSerializer(data=valid_data, context=context)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid old password
        invalid_old_password = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = KennelPasswordChangeSerializer(data=invalid_old_password, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
        
        # Test password mismatch
        password_mismatch = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        serializer = KennelPasswordChangeSerializer(data=password_mismatch, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test same password
        same_password = {
            'old_password': 'oldpassword123',
            'new_password': 'oldpassword123',
            'confirm_password': 'oldpassword123'
        }
        serializer = KennelPasswordChangeSerializer(data=same_password, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test short password
        short_password = {
            'old_password': 'oldpassword123',
            'new_password': 'short',
            'confirm_password': 'short'
        }
        serializer = KennelPasswordChangeSerializer(data=short_password, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_kennel_password_change_serializer_create(self):
        """Test the serializer create method."""
        context = {'request': type('MockRequest', (), {'user': self.kennel})()}
        
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        serializer = KennelPasswordChangeSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        # Create (change password)
        serializer.create(serializer.validated_data)
        
        # Verify password was changed
        self.kennel.refresh_from_db()
        self.assertTrue(self.kennel.check_password('newpassword123'))
        self.assertFalse(self.kennel.check_password('oldpassword123'))

    def test_kennel_password_change_endpoint_authentication_required(self):
        """Test that authentication is required for the endpoint."""
        url = '/api/kennels/change-password/'
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        # Test without authentication
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_kennel_password_change_endpoint_success(self):
        """Test successful password change through the API endpoint."""
        # Authenticate the kennel user
        self.client.force_authenticate(user=self.kennel)
        
        url = '/api/kennels/change-password/'
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Password has been changed successfully.')
        
        # Verify password was actually changed
        self.kennel.refresh_from_db()
        self.assertTrue(self.kennel.check_password('newpassword123'))
        
        # Verify reset_password field remains unchanged
        self.assertEqual(self.kennel.reset_password, True)  # Should remain as it was

    def test_kennel_password_change_preserves_reset_password_false(self):
        """Test that password change preserves reset_password=False."""
        # Set reset_password to False initially
        self.kennel.reset_password = False
        self.kennel.save()
        
        # Authenticate the kennel user
        self.client.force_authenticate(user=self.kennel)
        
        url = '/api/kennels/change-password/'
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'anotherpassword123',
            'confirm_password': 'anotherpassword123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.kennel.refresh_from_db()
        self.assertTrue(self.kennel.check_password('anotherpassword123'))
        
        # Verify reset_password field remains False
        self.assertEqual(self.kennel.reset_password, False)

    def test_kennel_password_change_endpoint_validation_errors(self):
        """Test validation errors through the API endpoint."""
        # Authenticate the kennel user
        self.client.force_authenticate(user=self.kennel)
        
        url = '/api/kennels/change-password/'
        
        # Test wrong old password
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
        
        # Test password mismatch
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_kennel_password_change_only_allows_post(self):
        """Test that only POST method is allowed."""
        self.client.force_authenticate(user=self.kennel)
        url = '/api/kennels/change-password/'
        
        # Test GET method (should not be allowed)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PUT method (should not be allowed)
        response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE method (should not be allowed)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
