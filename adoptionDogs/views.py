from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from .models import AdoptionDog
from rest_framework.views import APIView
from rest_framework.response import Response
from . serializer import *

@api_view(['GET'])
def adoption_list(request):
    adoption_dog = AdoptionDog.objects.all()
    serializer = AdoptionDogSerializer(adoption_dog, many=True)
    return Response(serializer.data)

# Get the dog of the day
@api_view(['GET'])
def dog_of_the_day(request):
    adoption_dog = AdoptionDog.objects.order_by('created_at').first()
    if adoption_dog:
        serializer = AdoptionDogSerializer(adoption_dog)
        return Response(serializer.data)
    else:
        return Response({'message': 'No dogs available'}, status=404)



