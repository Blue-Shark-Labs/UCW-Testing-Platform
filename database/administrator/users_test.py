from uuid import UUID

import database.administrator.users as users_module


def test_update_user_writes_password_hash_when_provided(monkeypatch):
    executed = []

    class FakeCursor:
        rowcount = 1

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            executed.append((" ".join(query.split()), params))

    class FakeConnectionProvider:
        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(
        users_module, "PostgresConnectionProvider", FakeConnectionProvider
    )
    user_id = UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")

    updated = users_module.update_user(
        user_id,
        "Ada",
        "Lecturer",
        "ada@example.test",
        "lecturer",
        None,
        None,
        "hashed-password",
    )

    assert updated
    query, params = executed[0]
    assert "password_hash = COALESCE(%s, password_hash)" in query
    assert params == (
        "Ada",
        "Lecturer",
        "ada@example.test",
        "lecturer",
        "hashed-password",
        user_id,
    )


def test_list_users_filters_students_from_results_and_count(monkeypatch):
    executed = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            executed.append(" ".join(query.split()))

        def fetchone(self):
            return (0,)

        def fetchall(self):
            return []

    class FakeConnectionProvider:
        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(
        users_module, "PostgresConnectionProvider", FakeConnectionProvider
    )

    users, total = users_module.list_users("", 8, 0)

    assert users == []
    assert total == 0
    assert len(executed) == 2
    assert all(
        "role IN ('lecturer', 'admin')" in query for query in executed
    )
