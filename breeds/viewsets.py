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
from .serializers import BreedSerializer

class BreedViewSet(ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']  # Only allow GET requests

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
        Import breeds from an uploaded CSV file.
        
        Expected form data:
        - csv_file: The CSV file to upload
        - update: (optional) Boolean to update existing breeds
        - clear: (optional) Boolean to clear existing breeds before import
        """
        try:
            # Check if file was uploaded
            if 'csv_file' not in request.FILES:
                return Response({
                    'error': 'No CSV file provided',
                    'detail': 'Please upload a CSV file using the csv_file field'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            csv_file = request.FILES['csv_file']
            
            # Validate file type
            if not csv_file.name.lower().endswith('.csv'):
                return Response({
                    'error': 'Invalid file type',
                    'detail': 'Please upload a CSV file'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get options from request
            update_existing = request.data.get('update', 'false').lower() == 'true'
            clear_existing = request.data.get('clear', 'false').lower() == 'true'
            
            # Read and process CSV
            try:
                # Decode the file content
                csv_content = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                
                # Validate CSV headers
                required_fields = ['breed', 'group', 'size']
                if not all(field in csv_reader.fieldnames for field in required_fields):
                    missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
                    return Response({
                        'error': 'Invalid CSV format',
                        'detail': f'Missing required columns: {", ".join(missing_fields)}',
                        'available_columns': list(csv_reader.fieldnames),
                        'required_columns': required_fields
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Helper function to parse rating values
                def parse_rating(value):
                    """Convert rating string to integer or None."""
                    if not value or value.strip() == '':
                        return None
                    try:
                        return int(value.strip())
                    except (ValueError, TypeError):
                        return None
                
                # Clear existing breeds if requested
                if clear_existing:
                    Breed.objects.all().delete()
                
                # Process breeds
                results = {
                    'created': 0,
                    'updated': 0,
                    'errors': 0,
                    'skipped': 0,
                    'error_details': []
                }
                
                with transaction.atomic():
                    for row_number, row in enumerate(csv_reader, start=2):  # Start at 2 because of header
                        try:
                            # Clean and validate data
                            breed_name = row['breed'].strip()
                            group = row['group'].strip()
                            size = row['size'].strip()
                            
                            # Skip empty rows
                            if not breed_name:
                                results['skipped'] += 1
                                continue
                            
                            # Validate group
                            valid_groups = [choice[0] for choice in Breed._meta.get_field('group').choices]
                            if group not in valid_groups:
                                results['errors'] += 1
                                results['error_details'].append({
                                    'row': row_number,
                                    'breed': breed_name,
                                    'error': f'Invalid group "{group}". Valid groups: {", ".join(valid_groups)}'
                                })
                                continue
                            
                            # Validate size
                            valid_sizes = [choice[0] for choice in Breed._meta.get_field('size').choices]
                            if size not in valid_sizes:
                                results['errors'] += 1
                                results['error_details'].append({
                                    'row': row_number,
                                    'breed': breed_name,
                                    'error': f'Invalid size "{size}". Valid sizes: {", ".join(valid_sizes)}'
                                })
                                continue
                            
                            # Prepare breed data with all available fields
                            breed_data = {
                                'group': group,
                                'size': size if size else None,
                            }
                            
                            # Add all additional fields from CSV if they exist
                            field_mappings = {
                                'Lifespan': 'lifespan',
                                'Height': 'height', 
                                'Weight': 'weight',
                                'Friendliness': 'friendliness',
                                'Family Friendly': 'family_friendly',
                                'Child Friendly': 'child_friendly',
                                'Pet Friendly': 'pet_friendly',
                                'Stranger Friendly': 'stranger_friendly',
                                'Easy to Groom': 'easy_to_groom',
                                'Energy Levels': 'energy_levels',
                                'Health': 'health',
                                'Shedding Amout': 'shedding_amount',  # Note: typo in CSV
                                'Barks / Howls': 'barks_howls',       # Note: spaces in CSV
                                'Easy to Train': 'easy_to_train',
                                'Watch dog': 'guard_dog',  # Note: CSV has "Watch dog" not "Guard Dog"
                                'Playfulness': 'playfulness',
                                'Apartment Dog': 'apartment_dog',
                                'Can be Alone': 'can_be_alone',
                                'Good for Busy Owners': 'good_for_busy_owners',
                                'Good for New Owners': 'good_for_new_owners',
                                'Health Concerns': 'health_concerns',
                                'Short Description': 'short_description',
                                'Long Description': 'long_description',
                            }
                            
                            # Map CSV fields to model fields
                            for csv_field, model_field in field_mappings.items():
                                if csv_field in row and row[csv_field]:
                                    value = row[csv_field].strip()
                                    if csv_field in ['Friendliness', 'Family Friendly', 'Child Friendly', 
                                                    'Pet Friendly', 'Stranger Friendly', 'Easy to Groom',
                                                    'Energy Levels', 'Health', 'Shedding Amout', 
                                                    'Barks / Howls', 'Easy to Train', 'Watch dog',
                                                    'Playfulness', 'Apartment Dog', 'Can be Alone',
                                                    'Good for Busy Owners', 'Good for New Owners']:
                                        breed_data[model_field] = parse_rating(value)
                                    else:
                                        breed_data[model_field] = value
                            
                            # Create or update breed
                            if update_existing:
                                breed, created = Breed.objects.update_or_create(
                                    breed=breed_name,
                                    defaults=breed_data
                                )
                                if created:
                                    results['created'] += 1
                                else:
                                    results['updated'] += 1
                            else:
                                # Check if breed already exists
                                if Breed.objects.filter(breed=breed_name).exists():
                                    results['errors'] += 1
                                    results['error_details'].append({
                                        'row': row_number,
                                        'breed': breed_name,
                                        'error': 'Breed already exists. Use update=true to update existing breeds.'
                                    })
                                    continue
                                
                                Breed.objects.create(
                                    breed=breed_name,
                                    **breed_data
                                )
                                results['created'] += 1
                        
                        except Exception as e:
                            results['errors'] += 1
                            results['error_details'].append({
                                'row': row_number,
                                'breed': row.get('breed', ''),
                                'error': str(e)
                            })
                
                # Add summary information
                results['total_breeds_in_database'] = Breed.objects.count()
                
                # Determine response status
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
