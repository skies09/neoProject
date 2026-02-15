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
        Match dogs based on user preferences. All fields optional; empty string = no preference.
        Returns up to 20 dogs with match_rate > 0%, sorted by match rate descending.
        """
        request_serializer = DogMatchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': request_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        prefs = request_serializer.validated_data

        def has_pref(key):
            v = prefs.get(key)
            if v is None:
                return False
            if isinstance(v, str) and not v.strip():
                return False
            return True

        if not any(has_pref(k) for k in prefs):
            return Response({
                'error': 'At least one preference must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        if has_pref('age_min') and has_pref('age_max') and prefs['age_min'] > prefs['age_max']:
            return Response({'error': 'age_min cannot be greater than age_max'}, status=status.HTTP_400_BAD_REQUEST)
        if has_pref('weight_min') and has_pref('weight_max') and prefs['weight_min'] > prefs['weight_max']:
            return Response({'error': 'weight_min cannot be greater than weight_max'}, status=status.HTTP_400_BAD_REQUEST)

        dogs = Dog.objects.select_related('kennel').all()

        if has_pref('age_min') or has_pref('age_max'):
            age_min, age_max = prefs.get('age_min'), prefs.get('age_max')
            q = Q()
            if age_min is not None and age_max is not None:
                q = Q(age__gte=age_min - 5, age__lte=age_max + 5) | Q(age__isnull=True)
            elif age_min is not None:
                q = Q(age__gte=age_min - 5) | Q(age__isnull=True)
            else:
                q = Q(age__lte=age_max + 5) | Q(age__isnull=True)
            dogs = dogs.filter(q)

        if has_pref('weight_min') or has_pref('weight_max'):
            w_min, w_max = prefs.get('weight_min'), prefs.get('weight_max')
            q = Q()
            if w_min is not None and w_max is not None:
                q = Q(weight__gte=w_min - 20, weight__lte=w_max + 20) | Q(weight__isnull=True)
            elif w_min is not None:
                q = Q(weight__gte=w_min - 20) | Q(weight__isnull=True)
            else:
                q = Q(weight__lte=w_max + 20) | Q(weight__isnull=True)
            dogs = dogs.filter(q)

        # Do not pre-filter by breed (or gender/size): score all candidates and return top 5 by match rate
        # so we can always return 5 matches when available.

        if prefs.get('good_with_children') is True:
            dogs = dogs.filter(good_with_children=True)
        if prefs.get('good_with_dogs') is True:
            dogs = dogs.filter(good_with_dogs=True)
        if prefs.get('good_with_cats') is True:
            dogs = dogs.filter(good_with_cats=True)

        # Leniency order to get 5 results: is_crossbreed → gender → age → size → breed.
        # Pool = all dogs passing good_with (and age/weight). For step 0 only, filter is_crossbreed when user said false.
        TOTAL_QUESTIONS = 9
        TARGET_MIN = 5
        TARGET_MAX = 20
        MIN_MATCH_RATE = 50
        pool = dogs

        def score_dog(dog, lenient):
            """lenient: dict with keys is_crossbreed, gender, age, size, breed (True = give 11% for that criterion)."""
            matches = 0

            if has_pref('gender'):
                if lenient.get('gender') or dog.gender == prefs['gender']:
                    matches += 1
            else:
                matches += 1

            if has_pref('size'):
                if lenient.get('size') or dog.size == prefs['size']:
                    matches += 1
            else:
                matches += 1

            age_min, age_max = prefs.get('age_min'), prefs.get('age_max')
            if age_min is not None or age_max is not None:
                if lenient.get('age'):
                    matches += 1
                elif dog.age is not None:
                    if age_min is not None and age_max is not None:
                        if age_min <= dog.age <= age_max:
                            matches += 1
                    elif age_min is not None:
                        if dog.age >= age_min:
                            matches += 1
                    else:
                        if dog.age <= age_max:
                            matches += 1
            else:
                matches += 1

            w_min, w_max = prefs.get('weight_min'), prefs.get('weight_max')
            if w_min is not None or w_max is not None:
                if dog.weight is not None:
                    if w_min is not None and w_max is not None:
                        if w_min <= dog.weight <= w_max:
                            matches += 1
                    elif w_min is not None:
                        if dog.weight >= w_min:
                            matches += 1
                    else:
                        if dog.weight <= w_max:
                            matches += 1
            else:
                matches += 1

            for key in ('good_with_dogs', 'good_with_cats', 'good_with_children'):
                pref_val = prefs.get(key)
                if pref_val is True:
                    if getattr(dog, key, None) is True:
                        matches += 1
                elif pref_val is False:
                    matches += 1
                else:
                    matches += 1

            if prefs.get('is_crossbreed') is not None:
                if lenient.get('is_crossbreed') or getattr(dog, 'is_crossbreed', None) == prefs['is_crossbreed']:
                    matches += 1
            else:
                matches += 1

            if has_pref('breed'):
                if lenient.get('breed') or (dog.breed and dog.breed.strip().lower() == prefs['breed'].strip().lower()):
                    matches += 1
            else:
                matches += 1

            return round((matches / TOTAL_QUESTIONS) * 100)

        leniency_order = [
            {'is_crossbreed': False, 'gender': False, 'age': False, 'size': False, 'breed': False},
            {'is_crossbreed': True, 'gender': False, 'age': False, 'size': False, 'breed': False},
            {'is_crossbreed': True, 'gender': True, 'age': False, 'size': False, 'breed': False},
            {'is_crossbreed': True, 'gender': True, 'age': True, 'size': False, 'breed': False},
            {'is_crossbreed': True, 'gender': True, 'age': True, 'size': True, 'breed': False},
            {'is_crossbreed': True, 'gender': True, 'age': True, 'size': True, 'breed': True},
        ]

        top_results = []
        all_scored_count = 0
        by_rate = []

        for step, lenient in enumerate(leniency_order):
            if step == 0 and prefs.get('is_crossbreed') is False:
                candidate_pool = pool.filter(is_crossbreed=False)
            else:
                candidate_pool = pool
            dogs_list = list(candidate_pool)
            all_scored_count = len(dogs_list)
            scored = [(dog, score_dog(dog, lenient)) for dog in dogs_list]
            by_rate = [(d, r) for d, r in scored if r > MIN_MATCH_RATE]
            # Primary: match rate desc. Secondary: same rate → breed match first (requested breed above others).
            breed_pref = prefs.get('breed') and prefs['breed'].strip().lower()
            def sort_key(item):
                dog, rate = item
                breed_match = 1 if (breed_pref and dog.breed and dog.breed.strip().lower() == breed_pref) else 0
                return (rate, breed_match)
            by_rate.sort(key=sort_key, reverse=True)
            top_results = by_rate[:TARGET_MAX]
            if len(top_results) >= TARGET_MIN:
                break

        results = [
            {'dog': DogSerializer(match_dog).data, 'match_rate': rate}
            for match_dog, rate in top_results
        ]

        return Response({
            'matches': results,
            'total_dogs_compared': all_scored_count,
            'total_matches_found': len(by_rate),
            'preferences_used': {k: v for k, v in prefs.items() if has_pref(k)}
        }, status=status.HTTP_200_OK)
