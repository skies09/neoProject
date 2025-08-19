import csv
import io
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction

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
                            
                            # Create or update breed
                            if update_existing:
                                breed, created = Breed.objects.update_or_create(
                                    breed=breed_name,
                                    defaults={
                                        'group': group,
                                        'size': size,
                                    }
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
                                    group=group,
                                    size=size,
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
