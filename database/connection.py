import os
from contextlib import contextmanager

import psycopg
from dotenv import dotenv_values, load_dotenv

load_dotenv()


class PostgresConnectionProvider:
    """Provides PostgreSQL cursors via a context manager.

    Connection details are read from the DATABASE_URL (host), DATABASE_NAME,
    DATABASE_USER, and PASSWORD environment variables, falling back to local
    development defaults. USERNAME in .env remains supported for compatibility
    with existing configurations and avoids Windows' built-in USERNAME value.
    """

    def __init__(self, conninfo: str | None = None):
        self._conninfo = conninfo or self._build_conninfo()

    @staticmethod
    def _build_conninfo() -> str:
        dotenv_config = dotenv_values()
        database_user = (
            os.environ.get("DATABASE_USER")
            or dotenv_config.get("DATABASE_USER")
            or dotenv_config.get("USERNAME")
            or os.environ.get("USERNAME")
            or "postgres"
        )
        # make_conninfo escapes special characters (e.g. in PASSWORD) safely.
        return psycopg.conninfo.make_conninfo(
            host=os.environ.get("DATABASE_URL", "localhost"),
            port=os.environ.get("DATABASE_PORT", "5432"),
            dbname=os.environ.get("DATABASE_NAME", "reinforcement_testing"),
            user=database_user,
            password=os.environ.get("PASSWORD", "postgres"),
        )

    @contextmanager
    def cursor(self):
        with psycopg.connect(self._conninfo) as conn:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
