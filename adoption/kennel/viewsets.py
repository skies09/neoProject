from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework import status
from adoption.kennel.serializers import KennelSerializer, KennelPasswordChangeSerializer
from adoption.kennel.models import Kennel
from adoption.abstract.viewsets import AbstractViewSet


class KennelViewSet(AbstractViewSet):
    http_method_names = ("patch", "get")
    permission_classes = (IsAuthenticated,)
    serializer_class = KennelSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Kennel.objects.all()
        # Allow kennel users to see their own profile and other non-superuser profiles
        return Kennel.objects.exclude(is_superuser=True)

    def get_object(self):
        public_id = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
        try:
            obj = Kennel.objects.get(public_id=public_id)
        except Kennel.DoesNotExist:
            raise NotFound("Kennel not found")

        # Allow kennel users to view their own profile or if they're a superuser
        if obj != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("You can only view your own profile.")

        return obj

    # Update Kennel info - only allow kennel users to update their own profile
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Only allow kennel users to update their own profile
        if instance != request.user and not request.user.is_superuser:
            raise PermissionDenied("You can only update your own profile.")

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class KennelPasswordChangeViewSet(viewsets.ViewSet):
    """ViewSet for kennel users to change their password."""
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']  # Only allow POST requests

    def create(self, request):
        """Change the kennel user's password."""
        serializer = KennelPasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            return Response({
                "detail": "Password has been changed successfully."
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
