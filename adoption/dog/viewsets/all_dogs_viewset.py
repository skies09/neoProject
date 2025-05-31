# adoption/dog/viewsets/all_dogs_viewset.py

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from adoption.dog.models import Dog
from adoption.dog.serializers import DogSerializer

class AllDogsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dog.objects.all()
    serializer_class = DogSerializer
    permission_classes = [AllowAny]
