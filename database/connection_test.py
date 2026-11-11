import psycopg

from database import connection


def test_build_conninfo_prefers_username_from_dotenv_on_windows(monkeypatch):
    monkeypatch.setenv("USERNAME", "windows-account")
    monkeypatch.delenv("DATABASE_USER", raising=False)
    monkeypatch.setattr(connection, "dotenv_values", lambda: {"USERNAME": "database-account"})

    conninfo = connection.PostgresConnectionProvider._build_conninfo()

    assert psycopg.conninfo.conninfo_to_dict(conninfo)["user"] == "database-account"


def test_build_conninfo_allows_database_user_environment_override(monkeypatch):
    monkeypatch.setenv("DATABASE_USER", "environment-database-account")
    monkeypatch.setattr(connection, "dotenv_values", lambda: {"USERNAME": "database-account"})

    conninfo = connection.PostgresConnectionProvider._build_conninfo()

    assert psycopg.conninfo.conninfo_to_dict(conninfo)["user"] == "environment-database-account"
