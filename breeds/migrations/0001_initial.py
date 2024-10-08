# Generated by Django 4.0.1 on 2024-09-01 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Breed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('breed', models.CharField(max_length=32)),
                ('group', models.CharField(choices=[('Gundog', 'Gundog'), ('Hound', 'Hound'), ('Pastoral', 'Pastoral'), ('Terrier', 'Terrier'), ('Toy', 'Toy'), ('Utility', 'Utility'), ('Working', 'Working'), ('Crossbreed', 'Crossbreed'), ('Pure', 'Pure')], max_length=16)),
                ('size', models.CharField(choices=[('XS', 'x-small'), ('S', 'small'), ('M', 'medium'), ('L', 'large'), ('XL', 'x-large')], max_length=5)),
            ],
        ),
    ]
