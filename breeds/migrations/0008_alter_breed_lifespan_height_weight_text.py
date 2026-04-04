# TEXT columns: no varchar cap — fixes persistent "character varying(8)" on old Postgres.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("breeds", "0007_postgresql_widen_all_tiny_varchar"),
    ]

    operations = [
        migrations.AlterField(
            model_name="breed",
            name="lifespan",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="breed",
            name="height",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="breed",
            name="weight",
            field=models.TextField(blank=True, null=True),
        ),
    ]
