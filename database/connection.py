import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "dev.env")


class PostgresConnectionProvider:
    """Provides PostgreSQL cursors via a context manager.

    Connection details are read from DATABASE_URL (host), DATABASE_NAME,
    DATABASE_USER, and PASSWORD, falling back to legacy USERNAME and local
    development defaults.
    """

    def __init__(self, conninfo: str | None = None):
        self._conninfo = conninfo or self._build_conninfo()

    @staticmethod
    def _build_conninfo() -> str:
        # make_conninfo escapes special characters (e.g. in PASSWORD) safely.
        return psycopg.conninfo.make_conninfo(
            host=os.environ.get("DATABASE_URL", "localhost"),
            port=os.environ.get("DATABASE_PORT", "5432"),
            dbname=os.environ.get("DATABASE_NAME", "reinforcement_testing"),
            user=os.environ.get("DATABASE_USER") or os.environ.get("USERNAME", "postgres"),
            password=os.environ.get("PASSWORD", "postgres"),
        )

    @contextmanager
    def cursor(self):
        with psycopg.connect(self._conninfo) as conn:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
