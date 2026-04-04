# Introspect Postgres and widen any breeds_breed varchar still <= 8 chars (and breed < 64).
# Defensive: fixes DBs where prior AlterField/RunPython migrations did not actually alter columns.

from django.db import migrations


def _safe_pg_identifier(name):
    return name and all(c.islower() or c.isdigit() or c == "_" for c in name)


def widen_short_varchar_columns(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    Breed = apps.get_model("breeds", "Breed")
    table = Breed._meta.db_table
    if not _safe_pg_identifier(table):
        return

    qtable = connection.ops.quote_name(table)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_schema, column_name, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
              AND data_type = 'character varying'
              AND character_maximum_length IS NOT NULL
            ORDER BY table_schema, column_name
            """,
            [table],
        )
        rows = cursor.fetchall()

    for schema, col_name, cur_len in rows:
        if not _safe_pg_identifier(schema) or not _safe_pg_identifier(col_name):
            continue
        qschema = connection.ops.quote_name(schema)
        qcol = connection.ops.quote_name(col_name)
        qualified = f"{qschema}.{qtable}"

        if cur_len <= 8:
            sql = (
                f"ALTER TABLE {qualified} ALTER COLUMN {qcol} "
                f"TYPE varchar(48) USING {qcol}::varchar(48);"
            )
            schema_editor.execute(sql)
        elif col_name == "breed" and cur_len < 64:
            sql = (
                f"ALTER TABLE {qualified} ALTER COLUMN {qcol} "
                f"TYPE varchar(64) USING {qcol}::varchar(64);"
            )
            schema_editor.execute(sql)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("breeds", "0006_postgresql_widen_lifespan_height_weight"),
    ]

    operations = [
        migrations.RunPython(widen_short_varchar_columns, noop_reverse),
    ]
