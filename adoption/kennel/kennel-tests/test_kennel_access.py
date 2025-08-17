from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from adoption.dog.models import Dog

User = get_user_model()

class KennelAccessTest(APITestCase):
    def setUp(self):
        # Create a kennel
        self.kennel = User.objects.create_kennel(
            username='testkennel',
            email='test@kennel.com',
            password='temp123',
            name='Test Kennel'
        )
        
        # Create a dog for this kennel
        self.dog = Dog.objects.create(
            name='Buddy',
            gender='Male',
            age=3,
            size='M',
            weight=25,
            good_with_dogs=True,
            good_with_cats=True,
            good_with_children=True,
            breed='Golden Retriever',
            is_crossbreed=False,
            kennel=self.kennel
        )
        
    def test_kennel_can_access_own_profile(self):
        """Test that a kennel can access their own profile"""
        # Login
        login_url = reverse('api:auth-login-list')
        login_data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Get access token
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to access own kennel profile
        kennel_url = reverse('api:kennels-detail', kwargs={'public_id': self.kennel.public_id})
        response = self.client.get(kennel_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testkennel')
        
    def test_kennel_can_access_own_dogs_via_nested_url(self):
        """Test that a kennel can access their own dogs via nested URL"""
        # Login
        login_url = reverse('api:auth-login-list')
        login_data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Get access token
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to access own dogs via nested URL
        dogs_url = reverse('api:kennel-dogs-list', kwargs={'kennel_public_id': self.kennel.public_id})
        response = self.client.get(dogs_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Buddy')
        
    def test_kennel_cannot_access_other_kennel_dogs(self):
        """Test that a kennel cannot access another kennel's dogs"""
        # Create another kennel
        other_kennel = User.objects.create_kennel(
            username='otherkennel',
            email='other@kennel.com',
            password='temp123',
            name='Other Kennel'
        )
        
        # Login as first kennel
        login_url = reverse('api:auth-login-list')
        login_data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Get access token
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Try to access other kennel's dogs (should fail)
        dogs_url = reverse('api:kennel-dogs-list', kwargs={'kennel_public_id': other_kennel.public_id})
        response = self.client.get(dogs_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_kennel_can_create_dog_via_nested_url(self):
        """Test that a kennel can create a dog via nested URL"""
        # Login
        login_url = reverse('api:auth-login-list')
        login_data = {
            'username': 'testkennel',
            'password': 'temp123'
        }
        
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Get access token
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Create a dog via nested URL
        dogs_url = reverse('api:kennel-dogs-list', kwargs={'kennel_public_id': self.kennel.public_id})
        dog_data = {
            'name': 'Max',
            'gender': 'Male',
            'age': 4,
            'size': 'L',
            'weight': 30,
            'good_with_dogs': True,
            'good_with_cats': True,
            'good_with_children': True,
            'breed': 'Labrador',
            'is_crossbreed': False
        }
        
        response = self.client.post(dogs_url, dog_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Max')
        self.assertEqual(response.data['kennel']['username'], 'testkennel')
