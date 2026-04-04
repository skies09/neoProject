"""
Ensure Postgres columns can hold DogDB CSV strings, using the *current* DB connection.

Runs at CSV import time so it always matches DATABASE_URL used by the request (migrations may not).
"""
import logging

from django.db import connection
from django.db.utils import DatabaseError

from breeds.models import Breed

logger = logging.getLogger(__name__)


def ensure_breed_table_for_csv_import():
    if connection.vendor != "postgresql":
        return

    table = Breed._meta.db_table

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_schema, column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
              AND data_type IN ('character varying', 'text', 'character')
            ORDER BY table_schema, column_name
            """,
            [table],
        )
        rows = cursor.fetchall()

    if not rows:
        logger.warning("csv_import_schema: no columns found for table %s", table)
        return

    by_schema = {}
    for schema, col_name, data_type, char_max in rows:
        by_schema.setdefault(schema, []).append(
            (col_name, data_type, char_max)
        )

    for schema, cols in by_schema.items():
        qschema = connection.ops.quote_name(schema)
        qtable = connection.ops.quote_name(table)
        qualified = f"{qschema}.{qtable}"

        for col_name, data_type, char_max in cols:
            if not col_name or not all(
                c.islower() or c.isdigit() or c == "_" for c in col_name
            ):
                continue
            qcol = connection.ops.quote_name(col_name)

            # Any varchar still capped at 8 (or smaller, e.g. size=5) → TEXT
            if data_type == "character varying" and char_max is not None and char_max <= 8:
                sql = (
                    f"ALTER TABLE {qualified} ALTER COLUMN {qcol} "
                    f"TYPE text USING {qcol}::text"
                )
                _run_alter(sql, col_name)
                continue

            if col_name == "breed" and data_type in (
                "character varying",
                "character",
            ):
                if char_max is not None and char_max < 64:
                    sql = (
                        f"ALTER TABLE {qualified} ALTER COLUMN {qcol} "
                        f"TYPE varchar(64) USING {qcol}::varchar(64)"
                    )
                    _run_alter(sql, col_name)
                continue

            if col_name in ("short_description", "long_description") and data_type != "text":
                sql = (
                    f"ALTER TABLE {qualified} ALTER COLUMN {qcol} "
                    f"TYPE text USING {qcol}::text"
                )
                _run_alter(sql, col_name)


def _run_alter(sql, col_name):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
        logger.info("csv_import_schema: altered column %s", col_name)
    except DatabaseError as exc:
        msg = str(exc).lower()
        if any(s in msg for s in ("already", "identical", "is of type text")):
            return
        raise
