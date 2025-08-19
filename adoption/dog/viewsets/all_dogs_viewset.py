from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from adoption.dog.models import Dog
from adoption.dog.serializers import DogSerializer
import random


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
        good_with_dogs = request.data.get("goodWithDogs")
        good_with_cats = request.data.get("goodWithCats")
        good_with_children = request.data.get("goodWithChildren")

        # Define filtering options in order of importance
        # Iterations of search to find one dog
        filter_options = [
            {
                "gender": gender,
                "good_with_dogs": good_with_dogs,
                "good_with_cats": good_with_cats,
                "good_with_children": good_with_children,
            },
            {
                "good_with_dogs": good_with_dogs,
                "good_with_cats": good_with_cats,
                "good_with_children": good_with_children,
            },
            {},  # No filters, return oldest dog
        ]

        for filters in filter_options:
            dogs = Dog.objects.all()
            for key, value in filters.items():
                if value is not None:
                    # Permissive value
                    if key == "gender":
                        dogs = dogs.filter(gender__iexact=value)
                    else:
                        dogs = dogs.filter(**{key: value})
            dog = dogs.order_by("created").first()
            if dog:
                serializer = self.get_serializer(dog)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "No matching dog found."}, status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=["get"], url_path="dog-of-the-day")
    def dog_of_the_day(self, request):
        """
        Returns a random dog as the "dog of the day".
        """
        # Get all available dogs
        dogs = Dog.objects.all()

        if not dogs.exists():
            return Response(
                {"detail": "No dogs available."}, status=status.HTTP_404_NOT_FOUND
            )

        # Get a random dog
        random_dog = random.choice(dogs)
        serializer = self.get_serializer(random_dog)

        return Response(serializer.data, status=status.HTTP_200_OK)

        # Alternative implementation: Return the oldest dog

        # oldest_dog = dogs.order_by('created').first()
        # serializer = self.get_serializer(oldest_dog)
        # return Response(serializer.data, status=status.HTTP_200_OK)
