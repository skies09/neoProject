# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('adoption_kennel', '0001_initial'),
        ('shop', '0002_remove_productimage_product_and_more'),
    ]

    operations = [
        # Delete the old CartItem model
        migrations.DeleteModel(
            name='CartItem',
        ),
        
        # Remove the old Cart model
        migrations.DeleteModel(
            name='Cart',
        ),
        
        # Create the new simplified Cart model
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='adoption_kennel.kennel')),
            ],
            options={
                'verbose_name': 'Cart Item',
                'verbose_name_plural': 'Cart Items',
                'ordering': ['-added_at'],
            },
        ),
        
        # Add unique constraint
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_user_product_cart'),
        ),
    ]