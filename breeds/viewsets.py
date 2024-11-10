from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models import Breed
from .serializers import BreedSerializer

class BreedViewSet(ViewSet):
    permission_classes = [AllowAny]
    serializer_class = BreedSerializer

    def get_queryset(self):
        return Breed.objects.all()

    # Endpoint to list all breeds
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def list_all(self, request):
        breeds = self.get_queryset()
        serializer = self.serializer_class(breeds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Endpoint to get distinct breed groups
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='groups')
    def list_groups(self, request):
        groups = Breed.objects.values_list('group', flat=True).distinct().order_by('group')
        return Response(groups, status=status.HTTP_200_OK)

    # Endpoint to get breeds within a specific group
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='groups/(?P<group>[^/.]+)')
    def list_breeds_in_group(self, request, group=None):
        breeds = Breed.objects.filter(group=group)
        if not breeds.exists():
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(breeds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Endpoint to get details for a specific breed
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='detail')
    def breed_detail(self, request):
        breed_name = request.data.get('breed')
        
        if not breed_name:
            return Response({'error': 'No breed provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            single_breed = Breed.objects.get(breed=breed_name)
        except Breed.DoesNotExist:
            return Response({'error': 'Breed not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(single_breed)
        return Response(serializer.data, status=status.HTTP_200_OK)
