from django.shortcuts import render, get_object_or_404
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
