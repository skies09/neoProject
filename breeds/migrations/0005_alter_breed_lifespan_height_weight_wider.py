# Widen measurement text fields (DogDB exceeds legacy varchar(8) from 0002).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("breeds", "0004_alter_breed_long_description_alter_breed_short_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="breed",
            name="lifespan",
            field=models.CharField(blank=True, max_length=48, null=True),
        ),
        migrations.AlterField(
            model_name="breed",
            name="height",
            field=models.CharField(blank=True, max_length=48, null=True),
        ),
        migrations.AlterField(
            model_name="breed",
            name="weight",
            field=models.CharField(blank=True, max_length=48, null=True),
        ),
    ]
