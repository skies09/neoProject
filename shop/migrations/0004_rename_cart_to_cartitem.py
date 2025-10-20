# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_simplify_cart'),
    ]

    operations = [
        # Rename the model from Cart to CartItem
        migrations.RenameModel(
            old_name='Cart',
            new_name='CartItem',
        ),
    ]