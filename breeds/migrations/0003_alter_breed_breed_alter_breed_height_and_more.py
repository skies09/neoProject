# Generated manually for DogDB.csv import (longer breed names and measurements)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breeds', '0002_breed_apartment_dog_breed_barks_howls_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breed',
            name='breed',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='breed',
            name='height',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
        migrations.AlterField(
            model_name='breed',
            name='lifespan',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
        migrations.AlterField(
            model_name='breed',
            name='weight',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
    ]
