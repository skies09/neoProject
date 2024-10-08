# Generated by Django 4.0.1 on 2024-09-29 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kennels', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='kennel',
            name='contact_number',
            field=models.CharField(default=111111, max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kennel',
            name='email',
            field=models.EmailField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='kennel',
            name='location',
            field=models.CharField(default='here', max_length=256),
            preserve_default=False,
        ),
    ]
