from contextlib import contextmanager
from unittest.mock import MagicMock

from database.helpers import database_helpers


class FakeConnectionProvider:
    def __init__(self, rows):
        self.cursor_mock = MagicMock()
        self.cursor_mock.fetchall.return_value = rows

    @contextmanager
    def cursor(self):
        yield self.cursor_mock


def test_subject_leaderboard_uses_erd_student_relationship_and_approval(monkeypatch):
    rows = [("student-id", "Ava", "Morgan", 3, 92.5, 450)]
    provider = FakeConnectionProvider(rows)
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.get_subject_leaderboard("subject-id")

    query, parameters = provider.cursor_mock.execute.call_args.args
    assert "JOIN students AS student ON student.user_id = u.user_id" in query
    assert "student.is_approved = TRUE" in query
    assert "LIMIT 5" in query
    assert parameters == ("subject-id",)
    assert result == [
        {
            "user_id": "student-id",
            "first_name": "Ava",
            "last_name": "Morgan",
            "completed_test_count": 3,
            "average_percentage": 92.5,
            "total_points": 450,
        }
    ]
