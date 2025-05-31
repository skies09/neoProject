from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from adoption.abstract.viewsets import AbstractViewSet
from adoption.dog.models import Dog
from adoption.dog.serializers import DogSerializer
from adoption.auth.permissions import UserPermission
from rest_framework.exceptions import NotFound

class DogViewSet(AbstractViewSet):
    http_method_names = ("post", "get", "put", "delete")
    permission_classes = (UserPermission,)
    serializer_class = DogSerializer

    def get_queryset(self):
        kennel_pk = self.kwargs.get('kennel_public_id') 
        if kennel_pk:
            return Dog.objects.filter(kennel__public_id=kennel_pk)
        return Dog.objects.none()
    
    def get_object(self):
        try:
            obj = Dog.objects.get_object_by_public_id(self.kwargs["pk"])
            self.check_object_permissions(self.request, obj)
            return obj
        except Dog.DoesNotExist:
            raise NotFound("Dog not found.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object() 
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)