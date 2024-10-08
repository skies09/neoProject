# Generated by Django 4.0.1 on 2024-09-29 15:28

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Kennel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kennel_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name_plural': 'Kennels',
            },
        ),
    ]
