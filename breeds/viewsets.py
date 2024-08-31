from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from breeds.models import Breeds
from breeds.serializers import BreedSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

class BreedViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    # permission_classes = [AllowAny]
    serializer_class = BreedSerializer
    queryset = Breeds.objects.all()


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # @csrf_exempt
    # @action(detail=False, methods=['delete'], permission_classes=[AllowAny])
    # def delete_all(self, request, *args, **kwargs):
    #     count, _ = Dog.objects.all().delete()
    #     return Response({'message': f'{count} dogs were deleted.'}, status=status.HTTP_204_NO_CONTENT)
    