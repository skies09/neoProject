# Force PostgreSQL column types (covers DBs where 0003/0005 AlterField did not apply).

from django.db import migrations


def widen_measurement_columns(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "postgresql":
        return
    with conn.cursor() as cursor:
        for col in ("lifespan", "height", "weight"):
            cursor.execute(
                "ALTER TABLE breeds_breed "
                f"ALTER COLUMN {col} TYPE varchar(48) USING {col}::varchar(48);"
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("breeds", "0005_alter_breed_lifespan_height_weight_wider"),
    ]

    operations = [
        migrations.RunPython(widen_measurement_columns, noop_reverse),
    ]
