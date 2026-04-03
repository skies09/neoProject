import csv
import io
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction

from .models import Breed
from .serializers import BreedSerializer, BreedMatchRequestSerializer


def _parse_breed_csv_rating(value):
    """Same rules as import_dogdb_csv: 1–10 as-is; 11–100 → 1–10 scale."""
    if value is None or str(value).strip() == "":
        return None
    try:
        raw = int(round(float(str(value).strip())))
    except (ValueError, TypeError):
        return None
    if raw <= 0:
        return None
    if raw <= 10:
        return raw
    if raw <= 100:
        return max(1, min(10, round(raw / 10.0)))
    return 10


_BREED_GROUP_MAP = {
    "Gundog": "Gundog",
    "Hound": "Hound",
    "Pastoral": "Pastoral",
    "Terrier": "Terrier",
    "Toy": "Toy",
    "Utility": "Utility",
    "Working": "Working",
    "Crossbreed": "Crossbreed",
    "Pure": "Pure",
}

_BREED_SIZE_MAP = {
    "XS": "XS",
    "S": "S",
    "M": "M",
    "L": "L",
    "XL": "XL",
    "x-small": "XS",
    "small": "S",
    "medium": "M",
    "large": "L",
    "x-large": "XL",
}


def _valid_breed_groups():
    return {c[0] for c in Breed._meta.get_field("group").choices}


def _valid_breed_sizes():
    return {c[0] for c in Breed._meta.get_field("size").choices}


def _csv_column_map(fieldnames):
    """
    Map header lookups (exact + casefold) -> DictReader key on each row.
    Strips whitespace and leading BOM so Excel/UTF-8 exports still match.
    """
    m = {}
    for fn in fieldnames or []:
        if fn is None:
            continue
        logical = fn.strip().lstrip("\ufeff")
        if not logical:
            continue
        if logical not in m:
            m[logical] = fn
        cf = logical.casefold()
        if cf not in m:
            m[cf] = fn
    return m


def _row_get(row, col_map, *names):
    """First matching column (any casing) wins."""
    for name in names:
        key = col_map.get(name)
        if key is None and name:
            key = col_map.get(name.casefold())
        if key is not None:
            return row.get(key)
    return None


def _has_required_headers(col_map, headers):
    for h in headers:
        if h in col_map or h.casefold() in col_map:
            continue
        return False
    return True


def _normalize_breed_group_size(group_raw, size_raw):
    """
    Map CSV group/size strings to model values. Invalid group → (None, None, error).
    Empty or invalid size → None (matches import_dogdb_csv).
    """
    valid_g = _valid_breed_groups()
    valid_s = _valid_breed_sizes()
    group = (group_raw or "").strip()
    size = (size_raw or "").strip()
    mapped_g = _BREED_GROUP_MAP.get(group, group)
    if mapped_g not in valid_g:
        return (
            None,
            None,
            f'Invalid group "{group_raw}". Valid: {", ".join(sorted(valid_g))}',
        )
    if not size:
        return mapped_g, None, None
    mapped_s = _BREED_SIZE_MAP.get(size, size)
    if mapped_s not in valid_s:
        return mapped_g, None, None
    return mapped_g, mapped_s, None


# DogDB.csv column names → model fields (ratings parsed with _parse_breed_csv_rating)
_DOGDB_RATING_COLUMNS = {
    "Friendliness": "friendliness",
    "Family Friendly": "family_friendly",
    "Child Friendly": "child_friendly",
    "Pet Friendly": "pet_friendly",
    "Stranger Friendly": "stranger_friendly",
    "Easy to Groom": "easy_to_groom",
    "Energy Levels": "energy_levels",
    "Health": "health",
    "Shedding Amout": "shedding_amount",
    "Barks / Howls": "barks_howls",
    "Easy to Train": "easy_to_train",
    "Guard Dog": "guard_dog",
    "Playfulness": "playfulness",
    "Apartment Dog": "apartment_dog",
    "Can be Alone": "can_be_alone",
    "Good for Busy Owners": "good_for_busy_owners",
    "Good for New Owners": "good_for_new_owners",
}

_DOGDB_TEXT_COLUMNS = {
    "Lifespan": "lifespan",
    "Height": "height",
    "Weight": "weight",
    "Health Concerns": "health_concerns",
    "Short Description": "short_description",
    "Long Description": "long_description",
}


def _breed_row_from_dogdb(row, col_map):
    breed_name = (_row_get(row, col_map, "Breed") or "").strip()
    group_raw = _row_get(row, col_map, "Group") or ""
    size_raw = _row_get(row, col_map, "Size") or ""
    mapped_g, mapped_s, err = _normalize_breed_group_size(group_raw, size_raw)
    if err:
        return None, err
    data = {
        "breed": breed_name,
        "group": mapped_g,
        "size": mapped_s,
    }
    for csv_col, model_field in _DOGDB_TEXT_COLUMNS.items():
        v = (_row_get(row, col_map, csv_col) or "").strip()
        data[model_field] = v or None
    for csv_col, model_field in _DOGDB_RATING_COLUMNS.items():
        data[model_field] = _parse_breed_csv_rating(
            _row_get(row, col_map, csv_col) or ""
        )
    return data, None


# Optional columns when using simple lowercase headers (same semantics as DogDB extras)
_SIMPLE_EXTRA_RATING = {
    "Friendliness": "friendliness",
    "Family Friendly": "family_friendly",
    "Child Friendly": "child_friendly",
    "Pet Friendly": "pet_friendly",
    "Stranger Friendly": "stranger_friendly",
    "Easy to Groom": "easy_to_groom",
    "Energy Levels": "energy_levels",
    "Health": "health",
    "Shedding Amout": "shedding_amount",
    "Barks / Howls": "barks_howls",
    "Easy to Train": "easy_to_train",
    "Watch dog": "guard_dog",
    "Guard Dog": "guard_dog",
    "Playfulness": "playfulness",
    "Apartment Dog": "apartment_dog",
    "Can be Alone": "can_be_alone",
    "Good for Busy Owners": "good_for_busy_owners",
    "Good for New Owners": "good_for_new_owners",
}

_SIMPLE_EXTRA_TEXT = {
    "Lifespan": "lifespan",
    "Height": "height",
    "Weight": "weight",
    "Health Concerns": "health_concerns",
    "Short Description": "short_description",
    "Long Description": "long_description",
}


def _merge_simple_optional_columns(row, breed_data, col_map):
    """Apply optional Title Case columns if present (shared with DogDB-style files)."""
    for csv_col, model_field in _SIMPLE_EXTRA_TEXT.items():
        v = _row_get(row, col_map, csv_col)
        if v:
            breed_data[model_field] = str(v).strip() or None
    for csv_col, model_field in _SIMPLE_EXTRA_RATING.items():
        v = _row_get(row, col_map, csv_col)
        if v:
            breed_data[model_field] = _parse_breed_csv_rating(v)
    return breed_data


class BreedViewSet(ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']  # Allow GET and POST requests

    # Override list method to provide better response
    def list(self, request, *args, **kwargs):
        """List all breeds with optional filtering"""
        queryset = self.get_queryset()
        
        # Add filtering options
        group = request.query_params.get('group', None)
        if group:
            queryset = queryset.filter(group=group)
        
        size = request.query_params.get('size', None)
        if size:
            queryset = queryset.filter(size=size)
        
        # Add search functionality
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(breed__icontains=search)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

    # Endpoint to upload CSV file and import breeds
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='import-csv')
    def import_csv(self, request):
        """
        Import breeds from an uploaded CSV file (multipart form).

        Form fields:
        - csv_file: CSV file (required)
        - update: optional, "true" / "false" (default false)
        - clear: optional, "true" / "false" — delete all breeds before import

        Supported CSV layouts:
        - DogDB: columns Breed, Group, Size (plus optional DogDB trait columns)
        - Simple: columns breed, group, size (plus optional Title Case extras)
        """
        try:
            if 'csv_file' not in request.FILES:
                return Response({
                    'error': 'No CSV file provided',
                    'detail': 'Please upload a CSV file using the csv_file field'
                }, status=status.HTTP_400_BAD_REQUEST)

            csv_file = request.FILES['csv_file']

            if not csv_file.name.lower().endswith('.csv'):
                return Response({
                    'error': 'Invalid file type',
                    'detail': 'Please upload a CSV file'
                }, status=status.HTTP_400_BAD_REQUEST)

            update_existing = request.data.get('update', 'false').lower() == 'true'
            clear_existing = request.data.get('clear', 'false').lower() == 'true'

            try:
                csv_content = csv_file.read().decode('utf-8')
                if csv_content.startswith('\ufeff'):
                    csv_content = csv_content[1:]
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                fieldnames = csv_reader.fieldnames

                if not fieldnames:
                    return Response({
                        'error': 'Invalid CSV format',
                        'detail': 'CSV has no header row',
                    }, status=status.HTTP_400_BAD_REQUEST)

                col_map = _csv_column_map(fieldnames)
                dogdb_ok = _has_required_headers(col_map, ('Breed', 'Group', 'Size'))
                simple_ok = _has_required_headers(col_map, ('breed', 'group', 'size'))

                if dogdb_ok:
                    csv_format = 'dogdb'
                elif simple_ok:
                    csv_format = 'simple'
                else:
                    return Response({
                        'error': 'Invalid CSV format',
                        'detail': (
                            'Need either DogDB headers (Breed, Group, Size) or '
                            'simple headers (breed, group, size).'
                        ),
                        'available_columns': list(fieldnames),
                    }, status=status.HTTP_400_BAD_REQUEST)

                if clear_existing:
                    Breed.objects.all().delete()

                results = {
                    'csv_format': csv_format,
                    'created': 0,
                    'updated': 0,
                    'errors': 0,
                    'skipped': 0,
                    'error_details': [],
                }

                for row_number, row in enumerate(csv_reader, start=2):
                    try:
                        if csv_format == 'dogdb':
                            breed_data, err = _breed_row_from_dogdb(row, col_map)
                            if err:
                                results['errors'] += 1
                                results['error_details'].append({
                                    'row': row_number,
                                    'breed': (
                                        _row_get(row, col_map, 'Breed') or ''
                                    ).strip(),
                                    'error': err,
                                })
                                continue
                            breed_name = breed_data['breed']
                            if not breed_name:
                                results['skipped'] += 1
                                continue
                            defaults = {k: v for k, v in breed_data.items() if k != 'breed'}
                        else:
                            breed_name = (
                                _row_get(row, col_map, 'breed') or ''
                            ).strip()
                            if not breed_name:
                                results['skipped'] += 1
                                continue
                            mapped_g, mapped_s, err = _normalize_breed_group_size(
                                _row_get(row, col_map, 'group') or '',
                                _row_get(row, col_map, 'size') or '',
                            )
                            if err:
                                results['errors'] += 1
                                results['error_details'].append({
                                    'row': row_number,
                                    'breed': breed_name,
                                    'error': err,
                                })
                                continue
                            defaults = {'group': mapped_g, 'size': mapped_s}
                            defaults = _merge_simple_optional_columns(
                                row, defaults, col_map
                            )

                        with transaction.atomic():
                            if update_existing:
                                _, created = Breed.objects.update_or_create(
                                    breed=breed_name,
                                    defaults=defaults,
                                )
                                if created:
                                    results['created'] += 1
                                else:
                                    results['updated'] += 1
                            else:
                                if Breed.objects.filter(breed=breed_name).exists():
                                    results['errors'] += 1
                                    results['error_details'].append({
                                        'row': row_number,
                                        'breed': breed_name,
                                        'error': (
                                            'Breed already exists. Use update=true to update.'
                                        ),
                                    })
                                    continue
                                Breed.objects.create(
                                    breed=breed_name,
                                    **defaults,
                                )
                                results['created'] += 1

                    except Exception as e:
                        results['errors'] += 1
                        results['error_details'].append({
                            'row': row_number,
                            'breed': (
                                _row_get(row, col_map, 'Breed', 'breed') or ''
                            ).strip(),
                            'error': str(e),
                        })

                results['total_breeds_in_database'] = Breed.objects.count()

                if results['errors'] > 0 and results['created'] == 0 and results['updated'] == 0:
                    response_status = status.HTTP_400_BAD_REQUEST
                    results['message'] = 'Import failed with errors'
                elif results['errors'] > 0:
                    response_status = status.HTTP_207_MULTI_STATUS
                    results['message'] = 'Import completed with some errors'
                else:
                    response_status = status.HTTP_200_OK
                    results['message'] = 'Import completed successfully'

                return Response(results, status=response_status)

            except UnicodeDecodeError:
                return Response({
                    'error': 'File encoding error',
                    'detail': 'Please ensure the CSV file is UTF-8 encoded'
                }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({
                    'error': 'CSV processing error',
                    'detail': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'Import failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Endpoint to match breeds based on preferences
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='match')
    def match_breeds(self, request):
        """
        Match breeds based on user preferences.
        
        Accepts preferences for various breed attributes and returns the top 5
        breeds that best match the criteria, along with match percentages.
        
        Example request body:
        {
            "size": "M",
            "pet_friendly": 8,
            "apartment_dog": 7,
            "easy_to_groom": 6,
            "family_friendly": 9,
            "energy_levels": 5
        }
        """
        # Validate request data
        request_serializer = BreedMatchRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': request_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        preferences = request_serializer.validated_data
        
        # Check if at least one preference is provided
        if not any(preferences.values()):
            return Response({
                'error': 'At least one preference must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all breeds
        breeds = Breed.objects.all()
        
        # Calculate match scores for each breed
        breed_matches = []
        
        for breed in breeds:
            match_scores = []
            total_weight = 0
            
            # Size matching (exact match)
            if preferences.get('size') is not None:
                if breed.size == preferences['size']:
                    match_scores.append(100.0)
                    total_weight += 1
                elif breed.size is not None:
                    match_scores.append(0.0)
                    total_weight += 1
            
            # Numeric field matching (1-10 scale)
            numeric_fields = [
                'pet_friendly', 'apartment_dog', 'easy_to_groom', 'family_friendly',
                'child_friendly', 'energy_levels', 'easy_to_train', 'can_be_alone',
                'good_for_busy_owners', 'good_for_new_owners', 'shedding_amount',
                'barks_howls', 'playfulness', 'friendliness', 'stranger_friendly',
                'guard_dog', 'health'
            ]
            
            for field in numeric_fields:
                user_pref = preferences.get(field)
                if user_pref is not None:
                    breed_value = getattr(breed, field, None)
                    if breed_value is not None:
                        # Calculate match percentage based on how close values are
                        # Perfect match (same value) = 100%
                        # Difference of 1 = 90%, difference of 2 = 80%, etc.
                        # Minimum match = 0% for difference >= 10
                        difference = abs(user_pref - breed_value)
                        match_percentage = max(0, 100 - (difference * 10))
                        match_scores.append(match_percentage)
                        total_weight += 1
            
            # Calculate overall match rate
            if total_weight > 0 and match_scores:
                overall_match = sum(match_scores) / total_weight
                breed_matches.append({
                    'breed': breed,
                    'match_rate': round(overall_match, 2)
                })
        
        # Sort by match rate (descending) and filter out 0% matches
        breed_matches.sort(key=lambda x: x['match_rate'], reverse=True)
        # Only include breeds with match rate greater than 0%
        non_zero_matches = [match for match in breed_matches if match['match_rate'] > 0]
        # Get top 5 (or fewer if less than 5 have > 0% match)
        top_5_matches = non_zero_matches[:5]
        
        # Serialize results
        results = []
        for match in top_5_matches:
            breed_serializer = BreedSerializer(match['breed'])
            results.append({
                'breed': breed_serializer.data,
                'match_rate': match['match_rate']
            })
        
        return Response({
            'matches': results,
            'total_breeds_compared': len(breed_matches),
            'preferences_used': {k: v for k, v in preferences.items() if v is not None}
        }, status=status.HTTP_200_OK)
