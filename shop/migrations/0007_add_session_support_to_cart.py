# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_rename_featured_to_bestseller'),
    ]

    operations = [
        # Add session_key field to CartItem
        migrations.AddField(
            model_name='cartitem',
            name='session_key',
            field=models.CharField(blank=True, help_text='Session key for anonymous users', max_length=40, null=True),
        ),
        
        # Make user field nullable
        migrations.AlterField(
            model_name='cartitem',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='cart_items', to='adoption_kennel.kennel'),
        ),
        
        # Update unique constraint to support both user and session_key
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('user', 'product'), ('session_key', 'product')},
        ),
    ]