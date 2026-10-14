import os
from contextlib import contextmanager

import psycopg


class PostgresConnectionProvider:
    """Provides PostgreSQL cursors via a context manager.

    The DSN is read from the DATABASE_URL environment
    variable, falling back to a local development default.
    """

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn or os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/reinforcement_testing",
        )

    @contextmanager
    def cursor(self):
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
