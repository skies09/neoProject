import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from breeds.models import Breed


class Command(BaseCommand):
    help = 'Import breeds from DogDB.csv file with proper field mapping'

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
                
                # Validate CSV headers
                required_fields = ['Breed', 'Group', 'Size']
                if not all(field in reader.fieldnames for field in required_fields):
                    missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                    raise CommandError(
                        f'CSV file is missing required columns: {", ".join(missing_fields)}\n'
                        f'Available columns: {", ".join(reader.fieldnames)}'
                    )
                
                self.stdout.write(f'Found columns: {", ".join(reader.fieldnames)}')
                
                # Import breeds
                created_count = 0
                updated_count = 0
                error_count = 0
                
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
                                continue
                            
                            # Map group values to valid choices
                            group_mapping = {
                                'Gundog': 'Gundog',
                                'Hound': 'Hound',
                                'Pastoral': 'Pastoral',
                                'Terrier': 'Terrier',
                                'Toy': 'Toy',
                                'Utility': 'Utility',
                                'Working': 'Working',
                                'Crossbreed': 'Crossbreed',
                                'Pure': 'Pure',
                            }
                            
                            mapped_group = group_mapping.get(group, group)
                            
                            # Map size values to valid choices
                            size_mapping = {
                                'XS': 'XS',
                                'S': 'S',
                                'M': 'M',
                                'L': 'L',
                                'XL': 'XL',
                                'x-small': 'XS',
                                'small': 'S',
                                'medium': 'M',
                                'large': 'L',
                                'x-large': 'XL',
                            }
                            
                            mapped_size = size_mapping.get(size, size)
                            
                            # Validate group
                            valid_groups = [choice[0] for choice in Breed._meta.get_field('group').choices]
                            if mapped_group not in valid_groups:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Row {row_number}: Invalid group "{group}" (mapped to "{mapped_group}") for breed "{breed_name}". '
                                        f'Valid groups: {", ".join(valid_groups)}'
                                    )
                                )
                                error_count += 1
                                continue
                            
                            # Handle empty size - set to None (will be blank in database)
                            if not mapped_size:
                                mapped_size = None
                            else:
                                # Validate size
                                valid_sizes = [choice[0] for choice in Breed._meta.get_field('size').choices]
                                if mapped_size not in valid_sizes:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'Row {row_number}: Invalid size "{size}" (mapped to "{mapped_size}") for breed "{breed_name}". '
                                            f'Setting to None. Valid sizes: {", ".join(valid_sizes)}'
                                        )
                                    )
                                    mapped_size = None
                            
                            # Prepare breed data
                            breed_data = {
                                'breed': breed_name,
                                'group': mapped_group,
                                'size': mapped_size,
                                'lifespan': row.get('Lifespan', '').strip() or None,
                                'height': row.get('Height', '').strip() or None,
                                'weight': row.get('Weight', '').strip() or None,
                                'friendliness': self._parse_rating(row.get('Friendliness', '')),
                                'family_friendly': self._parse_rating(row.get('Family Friendly', '')),
                                'child_friendly': self._parse_rating(row.get('Child Friendly', '')),
                                'pet_friendly': self._parse_rating(row.get('Pet Friendly', '')),
                                'stranger_friendly': self._parse_rating(row.get('Stranger Friendly', '')),
                                'easy_to_groom': self._parse_rating(row.get('Easy to Groom', '')),
                                'energy_levels': self._parse_rating(row.get('Energy Levels', '')),
                                'health': self._parse_rating(row.get('Health', '')),
                                'shedding_amount': self._parse_rating(row.get('Shedding Amout', '')),  # Note: typo in CSV
                                'barks_howls': self._parse_rating(row.get('Barks / Howls', '')),
                                'easy_to_train': self._parse_rating(row.get('Easy to Train', '')),
                                'guard_dog': self._parse_rating(row.get('Guard Dog', '')),
                                'playfulness': self._parse_rating(row.get('Playfulness', '')),
                                'apartment_dog': self._parse_rating(row.get('Apartment Dog', '')),
                                'can_be_alone': self._parse_rating(row.get('Can be Alone', '')),
                                'good_for_busy_owners': self._parse_rating(row.get('Good for Busy Owners', '')),
                                'good_for_new_owners': self._parse_rating(row.get('Good for New Owners', '')),
                                'health_concerns': row.get('Health Concerns', '').strip() or None,
                                'short_description': row.get('Short Description', '').strip() or None,
                                'long_description': row.get('Long Description', '').strip() or None,
                            }
                            
                            # Create or update breed
                            if options['update']:
                                breed, created = Breed.objects.update_or_create(
                                    breed=breed_name,
                                    defaults=breed_data
                                )
                                if created:
                                    created_count += 1
                                    self.stdout.write(f'Created: {breed_name}')
                                else:
                                    updated_count += 1
                                    self.stdout.write(f'Updated: {breed_name}')
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
                                
                                breed = Breed.objects.create(**breed_data)
                                created_count += 1
                                self.stdout.write(f'Created: {breed_name}')
                        
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
                if error_count > 0:
                    self.stdout.write(self.style.WARNING(f'Errors encountered: {error_count}'))
                
                total_breeds = Breed.objects.count()
                self.stdout.write(f'Total breeds in database: {total_breeds}')
        
        except FileNotFoundError:
            raise CommandError(f'Could not find CSV file: {csv_file_path}')
        except Exception as e:
            raise CommandError(f'Error processing CSV file: {str(e)}')
    
    def _parse_rating(self, value):
        """Parse rating values from CSV"""
        if not value or value.strip() == '':
            return None
        try:
            rating = int(value.strip())
            if 1 <= rating <= 10:
                return rating
            else:
                return None
        except (ValueError, TypeError):
            return None
