from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from adoption.dog.models import Dog, SIZES
from adoption.dog.serializers import DogSerializer, DogMatchRequestSerializer
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
        Returns up to three random dogs as "The Neo Trio"".
        """
        # Get all available dogs
        dogs = Dog.objects.all()

        if not dogs.exists():
            return Response(
                {"detail": "No dogs available."}, status=status.HTTP_404_NOT_FOUND
            )

        # Select up to three unique random dogs
        dog_list = list(dogs)
        sample_size = 3 if len(dog_list) >= 3 else len(dog_list)
        random_dogs = random.sample(dog_list, k=sample_size)
        serializer = self.get_serializer(random_dogs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

        # Alternative implementation: Return the oldest dog

        # oldest_dog = dogs.order_by('created').first()
        # serializer = self.get_serializer(oldest_dog)
        # return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='match')
    def match_dogs(self, request):
        """
        Match dogs based on user preferences.
        
        Accepts preferences for various dog attributes and returns the top 20
        dogs that best match the criteria, along with match percentages.
        
        Example request body:
        {
            "size": "M",
            "good_with_children": true,
            "good_with_dogs": true,
            "age_min": 1,
            "age_max": 5
        }
        """
        # Validate request data
        request_serializer = DogMatchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': request_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        preferences = request_serializer.validated_data
        
        # Check if at least one preference is provided
        if not any(v is not None for v in preferences.values()):
            return Response({
                'error': 'At least one preference must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate age range
        if preferences.get('age_min') is not None and preferences.get('age_max') is not None:
            if preferences['age_min'] > preferences['age_max']:
                return Response({
                    'error': 'age_min cannot be greater than age_max'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate weight range
        if preferences.get('weight_min') is not None and preferences.get('weight_max') is not None:
            if preferences['weight_min'] > preferences['weight_max']:
                return Response({
                    'error': 'weight_min cannot be greater than weight_max'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start with all dogs, but pre-filter using database queries for exact matches
        # This reduces the number of dogs we need to process in Python
        dogs = Dog.objects.select_related('kennel').all()
        
        # Don't pre-filter exact match fields (gender, size, boolean) - let Python scoring handle them
        # This ensures we don't accidentally exclude dogs that could still match on other criteria
        # The scoring algorithm will handle exact matches efficiently in Python
        
        # Pre-filter age range at database level (this helps but we still need to calculate match %)
        # Only filter if age is specified, and ensure we don't filter out dogs with null age
        age_min = preferences.get('age_min')
        age_max = preferences.get('age_max')
        if age_min is not None or age_max is not None:
            # Build age filter - include dogs with null age for scoring
            age_filters = Q()
            if age_min is not None and age_max is not None:
                # Filter to dogs within range or close to it (within 5 years for scoring)
                # Also include dogs with null age (they'll be scored in Python)
                age_filters = Q(age__gte=age_min - 5, age__lte=age_max + 5) | Q(age__isnull=True)
            elif age_min is not None:
                age_filters = Q(age__gte=age_min - 5) | Q(age__isnull=True)
            elif age_max is not None:
                age_filters = Q(age__lte=age_max + 5) | Q(age__isnull=True)
            dogs = dogs.filter(age_filters)
        
        # Pre-filter weight range at database level
        # Only filter if weight is specified, and ensure we don't filter out dogs with null weight
        weight_min = preferences.get('weight_min')
        weight_max = preferences.get('weight_max')
        if weight_min is not None or weight_max is not None:
            # Build weight filter - include dogs with null weight for scoring
            weight_filters = Q()
            if weight_min is not None and weight_max is not None:
                # Filter to dogs within range or close to it (within 20kg for scoring)
                # Also include dogs with null weight (they'll be scored in Python)
                weight_filters = Q(weight__gte=weight_min - 20, weight__lte=weight_max + 20) | Q(weight__isnull=True)
            elif weight_min is not None:
                weight_filters = Q(weight__gte=weight_min - 20) | Q(weight__isnull=True)
            elif weight_max is not None:
                weight_filters = Q(weight__lte=weight_max + 20) | Q(weight__isnull=True)
            dogs = dogs.filter(weight_filters)
        
        # Pre-filter breed if specified (case-insensitive partial match)
        if preferences.get('breed') is not None and preferences['breed'].strip():
            breed_pref = preferences['breed'].strip()
            dogs = dogs.filter(breed__icontains=breed_pref)
        
        # Convert to list to avoid multiple database queries during iteration
        # Only do this after filtering to minimize memory usage
        dogs_list = list(dogs)
        
        # Calculate match scores for each dog
        dog_matches = []
        
        for dog in dogs_list:
            match_scores = []
            total_weight = 0
            
            # Gender matching (exact match)
            if preferences.get('gender') is not None:
                if dog.gender == preferences['gender']:
                    match_scores.append(100.0)
                    total_weight += 1
                elif dog.gender is not None:
                    match_scores.append(0.0)
                    total_weight += 1
                # If dog.gender is None, skip this attribute (don't penalize)
            
            # Size matching (exact match)
            if preferences.get('size') is not None:
                if dog.size == preferences['size']:
                    match_scores.append(100.0)
                    total_weight += 1
                elif dog.size is not None:
                    match_scores.append(0.0)
                    total_weight += 1
                # If dog.size is None, skip this attribute (don't penalize)
            
            # Age matching (range matching)
            age_min = preferences.get('age_min')
            age_max = preferences.get('age_max')
            if age_min is not None or age_max is not None:
                if dog.age is not None:
                    if age_min is not None and age_max is not None:
                        # Check if dog age is within range
                        if age_min <= dog.age <= age_max:
                            match_scores.append(100.0)
                        else:
                            # Calculate distance from range
                            if dog.age < age_min:
                                distance = age_min - dog.age
                            else:
                                distance = dog.age - age_max
                            # Penalty: 10% per year difference, minimum 0%
                            match_percentage = max(0, 100 - (distance * 10))
                            match_scores.append(match_percentage)
                    elif age_min is not None:
                        # Only minimum specified
                        if dog.age >= age_min:
                            match_scores.append(100.0)
                        else:
                            distance = age_min - dog.age
                            match_percentage = max(0, 100 - (distance * 10))
                            match_scores.append(match_percentage)
                    elif age_max is not None:
                        # Only maximum specified
                        if dog.age <= age_max:
                            match_scores.append(100.0)
                        else:
                            distance = dog.age - age_max
                            match_percentage = max(0, 100 - (distance * 10))
                            match_scores.append(match_percentage)
                    total_weight += 1
            
            # Weight matching (range matching)
            weight_min = preferences.get('weight_min')
            weight_max = preferences.get('weight_max')
            if weight_min is not None or weight_max is not None:
                if dog.weight is not None:
                    if weight_min is not None and weight_max is not None:
                        # Check if dog weight is within range
                        if weight_min <= dog.weight <= weight_max:
                            match_scores.append(100.0)
                        else:
                            # Calculate distance from range
                            if dog.weight < weight_min:
                                distance = weight_min - dog.weight
                            else:
                                distance = dog.weight - weight_max
                            # Penalty: 1% per kg difference, minimum 0%
                            match_percentage = max(0, 100 - (distance * 1))
                            match_scores.append(match_percentage)
                    elif weight_min is not None:
                        # Only minimum specified
                        if dog.weight >= weight_min:
                            match_scores.append(100.0)
                        else:
                            distance = weight_min - dog.weight
                            match_percentage = max(0, 100 - (distance * 1))
                            match_scores.append(match_percentage)
                    elif weight_max is not None:
                        # Only maximum specified
                        if dog.weight <= weight_max:
                            match_scores.append(100.0)
                        else:
                            distance = dog.weight - weight_max
                            match_percentage = max(0, 100 - (distance * 1))
                            match_scores.append(match_percentage)
                    total_weight += 1
            
            # Boolean field matching (exact match)
            # Note: We filtered to include matches and nulls, so we need to check the actual value
            if preferences.get('good_with_dogs') is not None:
                dog_value = getattr(dog, 'good_with_dogs', None)
                if dog_value is not None:
                    if dog_value == preferences['good_with_dogs']:
                        match_scores.append(100.0)
                    else:
                        match_scores.append(0.0)
                    total_weight += 1
                # If dog_value is None, skip this attribute (don't add to total_weight)
            
            if preferences.get('good_with_cats') is not None:
                dog_value = getattr(dog, 'good_with_cats', None)
                if dog_value is not None:
                    if dog_value == preferences['good_with_cats']:
                        match_scores.append(100.0)
                    else:
                        match_scores.append(0.0)
                    total_weight += 1
            
            if preferences.get('good_with_children') is not None:
                dog_value = getattr(dog, 'good_with_children', None)
                if dog_value is not None:
                    if dog_value == preferences['good_with_children']:
                        match_scores.append(100.0)
                    else:
                        match_scores.append(0.0)
                    total_weight += 1
            
            if preferences.get('is_crossbreed') is not None:
                dog_value = getattr(dog, 'is_crossbreed', None)
                if dog_value is not None:
                    if dog_value == preferences['is_crossbreed']:
                        match_scores.append(100.0)
                    else:
                        match_scores.append(0.0)
                    total_weight += 1
            
            # Breed matching (case-insensitive partial match)
            # Already filtered with icontains, but calculate exact vs partial match score
            if preferences.get('breed') is not None and preferences['breed'].strip():
                breed_pref = preferences['breed'].strip().lower()
                if dog.breed:
                    dog_breed = dog.breed.lower()
                    if dog_breed == breed_pref:
                        match_scores.append(100.0)
                    else:
                        # Partial match (already filtered, so must be partial)
                        match_scores.append(80.0)
                    total_weight += 1
            
            # Calculate overall match rate
            if total_weight > 0 and match_scores:
                overall_match = sum(match_scores) / total_weight
                dog_matches.append({
                    'dog': dog,
                    'match_rate': round(overall_match, 2)
                })
        
        # Sort by match rate (descending) and filter out 0% matches
        # Use a more efficient approach: filter first, then sort only what we need
        non_zero_matches = [match for match in dog_matches if match['match_rate'] > 0]
        # Sort only the non-zero matches
        non_zero_matches.sort(key=lambda x: x['match_rate'], reverse=True)
        top_20_matches = non_zero_matches[:20]
        
        # Serialize results
        results = []
        for match in top_20_matches:
            dog_serializer = DogSerializer(match['dog'])
            results.append({
                'dog': dog_serializer.data,
                'match_rate': match['match_rate']
            })
        
        return Response({
            'matches': results,
            'total_dogs_compared': len(dog_matches),
            'total_matches_found': len(non_zero_matches),
            'preferences_used': {k: v for k, v in preferences.items() if v is not None}
        }, status=status.HTTP_200_OK)
