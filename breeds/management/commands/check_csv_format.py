import csv
import os
from django.core.management.base import BaseCommand, CommandError
from breeds.models import Breed


class Command(BaseCommand):
    help = 'Check the format of a CSV file before importing breeds'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to check'
        )
        parser.add_argument(
            '--sample-rows',
            type=int,
            default=10,
            help='Number of sample rows to display (default: 10)'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        sample_rows = options['sample_rows']
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file "{csv_file_path}" does not exist.')
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                self.stdout.write(f'Detected delimiter: "{delimiter}"')
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                # Check headers
                self.stdout.write(f'\nFound columns: {", ".join(reader.fieldnames)}')
                
                # Check required fields
                required_fields = ['breed', 'group', 'size']
                missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                
                if missing_fields:
                    self.stdout.write(
                        self.style.ERROR(f'\n❌ Missing required columns: {", ".join(missing_fields)}')
                    )
                else:
                    self.stdout.write(self.style.SUCCESS('\n✅ All required columns present'))
                
                # Get valid choices
                valid_groups = [choice[0] for choice in Breed._meta.get_field('group').choices]
                valid_sizes = [choice[0] for choice in Breed._meta.get_field('size').choices]
                
                self.stdout.write(f'\nValid groups: {", ".join(valid_groups)}')
                self.stdout.write(f'Valid sizes: {", ".join(valid_sizes)}')
                
                # Sample data analysis
                self.stdout.write(f'\n{"="*60}')
                self.stdout.write(f'SAMPLE DATA (first {sample_rows} rows):')
                self.stdout.write(f'{"="*60}')
                
                issues = []
                row_count = 0
                valid_rows = 0
                
                for row_number, row in enumerate(reader, start=2):  # Start at 2 because of header
                    if row_count >= sample_rows:
                        break
                    
                    row_count += 1
                    breed_name = row.get('breed', '').strip()
                    group = row.get('group', '').strip()
                    size = row.get('size', '').strip()
                    
                    # Display the row
                    self.stdout.write(f'\nRow {row_number}: {breed_name}')
                    self.stdout.write(f'  Group: "{group}"')
                    self.stdout.write(f'  Size: "{size}"')
                    
                    # Check for issues
                    row_issues = []
                    
                    if not breed_name:
                        row_issues.append('Empty breed name')
                    
                    if group and group not in valid_groups:
                        row_issues.append(f'Invalid group "{group}"')
                    elif not group:
                        row_issues.append('Missing group')
                    
                    if size and size not in valid_sizes:
                        row_issues.append(f'Invalid size "{size}"')
                    elif not size:
                        row_issues.append('Missing size')
                    
                    if row_issues:
                        self.stdout.write(self.style.WARNING(f'  Issues: {", ".join(row_issues)}'))
                        issues.extend(row_issues)
                    else:
                        self.stdout.write(self.style.SUCCESS('  ✅ Valid'))
                        valid_rows += 1
                
                # Count remaining rows
                remaining_rows = sum(1 for _ in reader)
                total_rows = row_count + remaining_rows
                
                # Summary
                self.stdout.write(f'\n{"="*60}')
                self.stdout.write('SUMMARY:')
                self.stdout.write(f'{"="*60}')
                
                self.stdout.write(f'Total rows in file: {total_rows + 1} (including header)')
                self.stdout.write(f'Data rows analyzed: {row_count}')
                self.stdout.write(f'Valid rows: {valid_rows}')
                self.stdout.write(f'Rows with issues: {row_count - valid_rows}')
                
                if remaining_rows > 0:
                    self.stdout.write(f'Remaining rows not shown: {remaining_rows}')
                
                # Recommendations
                self.stdout.write(f'\n{"="*60}')
                self.stdout.write('RECOMMENDATIONS:')
                self.stdout.write(f'{"="*60}')
                
                if missing_fields:
                    self.stdout.write(self.style.ERROR('❌ Fix missing columns before importing'))
                    
                if issues:
                    unique_issues = list(set(issues))
                    self.stdout.write(self.style.WARNING('⚠️  Fix the following issues:'))
                    for issue in unique_issues:
                        self.stdout.write(f'   - {issue}')
                    
                    # Specific recommendations for common issues
                    if any('Invalid group' in issue for issue in unique_issues):
                        self.stdout.write('\n   Group name suggestions:')
                        self.stdout.write('   - "Sporting" → "Gundog"')
                        self.stdout.write('   - "Herding" → "Pastoral"')
                        self.stdout.write('   - "Non-sporting" → "Utility"')
                    
                    if any('Invalid size' in issue for issue in unique_issues):
                        self.stdout.write('\n   Size name suggestions:')
                        self.stdout.write('   - "Extra Small" → "XS"')
                        self.stdout.write('   - "Small" → "S"')
                        self.stdout.write('   - "Medium" → "M"')
                        self.stdout.write('   - "Large" → "L"')
                        self.stdout.write('   - "Extra Large" → "XL"')
                
                if not missing_fields and not issues:
                    self.stdout.write(self.style.SUCCESS('✅ File looks good! Ready to import.'))
                    self.stdout.write('\nTo import, run:')
                    self.stdout.write(f'python manage.py import_breeds_csv "{csv_file_path}"')
                
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
