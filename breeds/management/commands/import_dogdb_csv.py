import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from breeds.models import Breed


class Command(BaseCommand):
    help = 'Import breeds from DogDB.csv format'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the DogDB.csv file to import'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing breeds instead of creating new ones'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing breeds before importing'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file "{csv_file_path}" does not exist.')
        
        # Clear existing breeds if requested
        if options['clear']:
            self.stdout.write('Clearing existing breeds...')
            Breed.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All existing breeds cleared.'))
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate CSV headers for DogDB format
                required_fields = ['Breed', 'Group', 'Size']
                if not all(field in reader.fieldnames for field in required_fields):
                    missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                    raise CommandError(
                        f'CSV file is missing required columns: {", ".join(missing_fields)}\n'
                        f'Available columns: {", ".join(reader.fieldnames)}\n'
                        f'Required columns: {", ".join(required_fields)}'
                    )
                
                self.stdout.write(f'Found columns: {", ".join(reader.fieldnames)}')
                
                # Import breeds
                created_count = 0
                updated_count = 0
                error_count = 0
                skipped_count = 0
                
                with transaction.atomic():
                    for row_number, row in enumerate(reader, start=2):  # Start at 2 because of header
                        try:
                            # Clean and validate data
                            breed_name = row['Breed'].strip()
                            group = row['Group'].strip()
                            size = row['Size'].strip()
                            
                            # Skip empty rows
                            if not breed_name:
                                self.stdout.write(
                                    self.style.WARNING(f'Row {row_number}: Skipping empty breed name')
                                )
                                skipped_count += 1
                                continue
                            
                            # Map group names to valid choices
                            group_mapping = {
                                'Toy': 'Toy',
                                'Hound': 'Hound',
                                'Terrier': 'Terrier',
                                'Utility': 'Utility',
                                'Working': 'Working',
                                'Pastoral': 'Pastoral',
                                'Gundog': 'Gundog',
                                'Sporting': 'Gundog',  # Map Sporting to Gundog
                                'Herding': 'Pastoral',  # Map Herding to Pastoral
                                'Non-sporting': 'Utility',  # Map Non-sporting to Utility
                            }
                            
                            if group not in group_mapping:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Row {row_number}: Unknown group "{group}" for breed "{breed_name}". '
                                        f'Mapping to "Utility".'
                                    )
                                )
                                group = 'Utility'
                            else:
                                group = group_mapping[group]
                            
                            # Map size names to valid choices
                            size_mapping = {
                                'XS': 'XS',
                                'S': 'S',
                                'M': 'M',
                                'L': 'L',
                                'XL': 'XL',
                                'Extra Small': 'XS',
                                'Small': 'S',
                                'Medium': 'M',
                                'Large': 'L',
                                'Extra Large': 'XL',
                                'X-Small': 'XS',
                                'X-Large': 'XL',
                            }
                            
                            if size not in size_mapping:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Row {row_number}: Unknown size "{size}" for breed "{breed_name}". '
                                        f'Mapping to "M".'
                                    )
                                )
                                size = 'M'
                            else:
                                size = size_mapping[size]
                            
                            # Create or update breed
                            if options['update']:
                                breed, created = Breed.objects.update_or_create(
                                    breed=breed_name,
                                    defaults={
                                        'group': group,
                                        'size': size,
                                    }
                                )
                                if created:
                                    created_count += 1
                                    self.stdout.write(f'Created: {breed_name} ({group}, {size})')
                                else:
                                    updated_count += 1
                                    self.stdout.write(f'Updated: {breed_name} ({group}, {size})')
                            else:
                                # Check if breed already exists
                                if Breed.objects.filter(breed=breed_name).exists():
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'Row {row_number}: Breed "{breed_name}" already exists. '
                                            'Use --update flag to update existing breeds.'
                                        )
                                    )
                                    error_count += 1
                                    continue
                                
                                breed = Breed.objects.create(
                                    breed=breed_name,
                                    group=group,
                                    size=size,
                                )
                                created_count += 1
                                self.stdout.write(f'Created: {breed_name} ({group}, {size})')
                        
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_number}: Error processing breed "{row.get("Breed", "")}" - {str(e)}')
                            )
                
                # Summary
                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS(f'Import completed!'))
                self.stdout.write(f'Breeds created: {created_count}')
                if options['update']:
                    self.stdout.write(f'Breeds updated: {updated_count}')
                self.stdout.write(f'Breeds skipped: {skipped_count}')
                if error_count > 0:
                    self.stdout.write(self.style.WARNING(f'Errors encountered: {error_count}'))
                
                total_breeds = Breed.objects.count()
                self.stdout.write(f'Total breeds in database: {total_breeds}')
        
        except FileNotFoundError:
            raise CommandError(f'Could not find CSV file: {csv_file_path}')
        except Exception as e:
            raise CommandError(f'Error processing CSV file: {str(e)}')
