# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_add_brand_remove_digital'),
    ]

    operations = [
        # Rename the field from is_featured to is_bestseller
        migrations.RenameField(
            model_name='product',
            old_name='is_featured',
            new_name='is_bestseller',
        ),
    ]