# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_update_order_fields_for_uk'),
        ('adoption_kennel', '0001_initial'), # Assuming Kennel is the User model
    ]

    operations = [
        # Make user field nullable and add session_key field
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='adoption_kennel.kennel'),
        ),
        migrations.AddField(
            model_name='order',
            name='session_key',
            field=models.CharField(blank=True, help_text='Session key for anonymous users', max_length=40, null=True),
        ),
    ]