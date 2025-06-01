from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from adoption.dog.models import Dog
from adoption.dog.serializers import DogSerializer


# Gets all the dogs
class AllDogsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dog.objects.all()
    serializer_class = DogSerializer
    permission_classes = [AllowAny]

    # This is the main feature!
    # Filters the dogs to find a single dog
    @action(detail=False, methods=["post"], url_path="filter")
    def filter_dogs(self, request):
        gender = request.data.get("gender")
        size = request.data.get("size")
        good_with_dogs = request.data.get("goodWithDogs")
        good_with_cats = request.data.get("goodWithCats")
        good_with_children = request.data.get("goodWithChildren")

        print(good_with_dogs)
        # Start with all dogs
        dogs = Dog.objects.all()

        # Filter by gender
        if gender:
            dogs = dogs.filter(gender__iexact=gender)

        # Filter by good with dogs
        if good_with_dogs is not None:
            dogs = dogs.filter(good_with_dogs=good_with_dogs)

        # Filter by good with cats
        if good_with_cats is not None:
            dogs = dogs.filter(good_with_cats=good_with_cats)

        # Filter by good with children
        if good_with_children is not None:
            dogs = dogs.filter(good_with_children=good_with_children)

        # if size:
        #     dogs = dogs.filter(size__iexact=size)

        serializer = self.get_serializer(dogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
