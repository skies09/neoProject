from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from .models import Breed
from rest_framework.views import APIView
from rest_framework.response import Response
from . serializer import *

@api_view(['GET'])
def breeds_list(request):
    breeds = Breed.objects.all()
    serializer = BreedSerializer(breeds, many=True)
    return Response(serializer.data)

# Get the groups available
@api_view(['GET'])
def breed_groups(request):
    groups =  Breed.objects.values_list('group', flat=True).distinct().order_by('group')
    return Response(groups)

# Get the breeds in the group
@api_view(['GET'])
def group_breeds(request, group):
    breeds = Breed.objects.filter(group=group)
    serializer = BreedSerializer(breeds, many=True)
    return Response(serializer.data)

# Get individual breed view
@api_view(['POST'])
def breed_detail(request):
    breed = request.data.get('breed')
    
    if not breed:
        return Response({'error': 'No breed provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        single_breed = Breed.objects.get(breed=breed)
    except Breed.DoesNotExist:
        return Response({'error': 'Breed not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BreedSerializer(single_breed)
    return Response(serializer.data)