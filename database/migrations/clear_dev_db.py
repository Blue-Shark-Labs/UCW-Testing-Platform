# Delete all rows from every table in the dev database, keeping the schema. Never run against prod.
# Run with `make clear-dev-db`, then `make migrate-dev-db` to re-seed.

import os
import sys

from psycopg import sql

from database.connection import PostgresConnectionProvider


def clear_dev_db():
    database_name = os.environ.get("DATABASE_NAME", "reinforcement_testing")
    if "prod" in database_name.lower() and "nonprod" not in database_name.lower():
        sys.exit(f"Refusing to clear '{database_name}': it looks like a production database.")

    answer = input(f"Delete ALL data in '{database_name}'? Type the database name to confirm: ")
    if answer.strip() != database_name:
        sys.exit("Aborted.")

    with PostgresConnectionProvider().cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = current_schema();")
        tables = [row[0] for row in cur.fetchall()]
        if tables:
            cur.execute(
                sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE;").format(
                    sql.SQL(", ").join(sql.Identifier(table) for table in tables)
                )
            )
    print(f"Cleared {len(tables)} tables in '{database_name}'.")


if __name__ == "__main__":
    clear_dev_db()
