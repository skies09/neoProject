# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_rename_cart_to_cartitem'),
    ]

    operations = [
        # Add brand field
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, help_text='Product brand name', max_length=100, null=True),
        ),
        
        # Remove is_digital field
        migrations.RemoveField(
            model_name='product',
            name='is_digital',
        ),
    ]