# Create the PostgreSQL schema.
# Run with `make setup-db` (or `python database/migrations/migrate.py`).
# No feature tables are defined yet — add CREATE TABLE statements here as the
# data model is agreed. The connection uses the DATABASE_URL environment
# variable via the shared connection provider.

from database.connection import PostgresConnectionProvider


def migrate():
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        # Add schema statements here, e.g.:
        # cur.execute("CREATE TABLE IF NOT EXISTS ...;")
        pass
    print("Migration complete: no tables defined yet.")


if __name__ == "__main__":
    migrate()
