from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from adoption.abstract.viewsets import AbstractViewSet
from adoption.dog.models import Dog
from adoption.dog.serializers import DogSerializer
from rest_framework.exceptions import NotFound, PermissionDenied


# ViewSet for kennels to manage their own dogs
class DogViewSet(AbstractViewSet):
    http_method_names = ("post", "get", "put", "patch", "delete")
    permission_classes = (IsAuthenticated,)
    serializer_class = DogSerializer

    def get_queryset(self):
        # Return only the logged-in user's dogs
        return Dog.objects.filter(kennel=self.request.user)

    def get_object(self):
        try:
            obj = Dog.objects.get_object_by_public_id(self.kwargs["pk"])
            # Check if the logged-in user owns this dog
            if obj.kennel != self.request.user:
                raise PermissionDenied("You can only access your own dogs.")
            return obj
        except Dog.DoesNotExist:
            raise NotFound("Dog not found.")

    def create(self, request, *args, **kwargs):
        # Pass the kennel_public_id in the context
        context = self.get_serializer_context()
        context["kennel_public_id"] = request.user.public_id

        serializer = self.get_serializer(data=request.data, context=context)
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
