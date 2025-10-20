# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_add_session_support_to_cart'),
    ]

    operations = [
        # Rename shipping_state to shipping_county
        migrations.RenameField(
            model_name='order',
            old_name='shipping_state',
            new_name='shipping_county',
        ),
        
        # Rename billing_state to billing_county
        migrations.RenameField(
            model_name='order',
            old_name='billing_state',
            new_name='billing_county',
        ),
        
        # Update shipping_county field to use UK_COUNTIES choices
        migrations.AlterField(
            model_name='order',
            name='shipping_county',
            field=models.CharField(choices=[('ENGLAND', 'England'), ('SCOTLAND', 'Scotland'), ('WALES', 'Wales'), ('NORTHERN_IRELAND', 'Northern Ireland')], default='ENGLAND', max_length=50),
        ),
        
        # Update billing_county field to use UK_COUNTIES choices
        migrations.AlterField(
            model_name='order',
            name='billing_county',
            field=models.CharField(choices=[('ENGLAND', 'England'), ('SCOTLAND', 'Scotland'), ('WALES', 'Wales'), ('NORTHERN_IRELAND', 'Northern Ireland')], default='ENGLAND', max_length=50),
        ),
        
        # Update shipping_postal_code field with UK-specific help text
        migrations.AlterField(
            model_name='order',
            name='shipping_postal_code',
            field=models.CharField(help_text='UK postcode (e.g., SW1A 1AA)', max_length=10),
        ),
        
        # Update billing_postal_code field with UK-specific help text
        migrations.AlterField(
            model_name='order',
            name='billing_postal_code',
            field=models.CharField(help_text='UK postcode (e.g., SW1A 1AA)', max_length=10),
        ),
        
        # Set default values for country fields
        migrations.AlterField(
            model_name='order',
            name='shipping_country',
            field=models.CharField(default='United Kingdom', max_length=100),
        ),
        
        migrations.AlterField(
            model_name='order',
            name='billing_country',
            field=models.CharField(default='United Kingdom', max_length=100),
        ),
    ]