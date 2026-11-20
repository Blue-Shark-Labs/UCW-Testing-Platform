from contextlib import contextmanager
from datetime import datetime
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
def test_get_assigned_tests_filters_by_assignment_and_attempt_user_id(monkeypatch):
    rows = [("42", "Algebra Basics", "Mathematics", 10)]
    provider = FakeConnectionProvider(rows)
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.get_assigned_tests("7")

    query, parameters = provider.cursor_mock.execute.call_args.args
    assert "FROM tests AS t" in query
    assert "JOIN test_assignments AS assignment" in query
    assert "assignment.student_id = %s" in query
    assert "attempt.user_id = assignment.student_id" in query
    assert "attempt.student_id" not in query
    assert parameters == ("7",)
    assert result == [
        {
            "test_id": "42",
            "test_name": "Algebra Basics",
            "subject_name": "Mathematics",
            "question_count": 10,
        }
    ]


def test_get_completed_tests_uses_attempt_user_id(monkeypatch):
    completed_at = datetime(2026, 11, 5, 14, 30)
    rows = [("81", "test-1", "Algebra Basics", "Mathematics", completed_at, 10, 92.5, 300)]
    provider = FakeConnectionProvider(rows)
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.get_completed_tests("7")

    query, parameters = provider.cursor_mock.execute.call_args.args
    assert "FROM test_attempts AS attempt" in query
    assert "JOIN subjects AS s" in query
    assert "attempt.user_id = %s" in query
    assert "attempt.student_id" not in query
    assert "attempt.completed_at IS NOT NULL" in query
    assert "t.question_count" in query
    assert "attempt_answers" not in query
    assert "GROUP BY" not in query
    assert parameters == ("7",)
    assert result == [
        {
            "attempt_id": "81",
            "test_id": "test-1",
            "test_name": "Algebra Basics",
            "subject_name": "Mathematics",
            "completed_at": completed_at,
            "question_count": 10,
            "percentage": 92.5,
            "total_points": 300,
        }
    ]
