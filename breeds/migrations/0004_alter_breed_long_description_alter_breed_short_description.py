# Full-length breed descriptions (no 256/528 char limits)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breeds', '0003_alter_breed_breed_alter_breed_height_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breed',
            name='long_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='breed',
            name='short_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
