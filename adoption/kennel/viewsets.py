from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from adoption.kennel.serializers import KennelSerializer
from adoption.kennel.models import Kennel
from adoption.abstract.viewsets import AbstractViewSet

class KennelViewSet(AbstractViewSet):
    http_method_names = ('patch', 'get')
    permission_classes = (AllowAny,)
    serializer_class = KennelSerializer
    lookup_field = "public_id"


    def get_queryset(self):
        if self.request.user.is_superuser:
            return Kennel.objects.all()
        return Kennel.objects.exclude(is_superuser=True)

    def get_object(self):
        public_id = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
        try:
            obj = Kennel.objects.get(public_id=public_id)
        except Kennel.DoesNotExist:
            raise NotFound("Kennel not found")
        self.check_object_permissions(self.request, obj)
        return obj

    # Update Kennel info
    def update(self, request, *args, **kwargs):
        instance = self.get_object()  #
        serializer = self.get_serializer(instance, data=request.data, partial=True) 
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
