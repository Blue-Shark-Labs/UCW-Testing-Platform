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


def test_get_assigned_tests_uses_attempt_user_id(monkeypatch):
    rows = [("42", "Algebra Basics", "Mathematics", 10)]
    provider = FakeConnectionProvider(rows)
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.get_assigned_tests("7")

    query, parameters = provider.cursor_mock.execute.call_args.args
    assert "FROM tests AS t" in query
    assert "JOIN test_assignments AS assignment" in query
    assert "assignment.student_id = %s" in query
    assert "attempt.user_id = %s" in query
    assert "attempt.student_id" not in query
    assert parameters == ("7", "7")
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
    rows = [("81", "Algebra Basics", completed_at, 10, 92.5, 300)]
    provider = FakeConnectionProvider(rows)
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.get_completed_tests("7")

    query, parameters = provider.cursor_mock.execute.call_args.args
    assert "FROM test_attempts AS attempt" in query
    assert "attempt.user_id = %s" in query
    assert "attempt.student_id" not in query
    assert "attempt.completed_at IS NOT NULL" in query
    assert parameters == ("7",)
    assert result == [
        {
            "attempt_id": "81",
            "test_name": "Algebra Basics",
            "completed_at": completed_at,
            "question_count": 10,
            "percentage": 92.5,
            "total_points": 300,
        }
    ]


def test_start_attempt_uses_existing_attempt_answer_columns(monkeypatch):
    class AttemptCursor:
        def __init__(self):
            self.one = None
            self.many = []
            self.executed = []

        def execute(self, query, parameters):
            self.executed.append((query, parameters))
            if "SELECT t.test_id, t.title" in query:
                self.one = ("test-id", "Algebra", "Mathematics", "subject-id", 1, None)
            elif "SELECT attempt_id" in query:
                self.one = None
            elif "SELECT q.question_id, q.question_text\n" in query:
                self.many = [("question-id", "Solve for x.")]
            elif "INSERT INTO test_attempts" in query:
                self.one = ("attempt-id",)
            elif "SELECT q.question_id, q.question_text, answer.selected_option_id" in query:
                self.many = [("question-id", "Solve for x.", None)]
            elif "SELECT option_id, option_text" in query:
                self.many = [
                    ("option-1", "4"),
                    ("option-2", "5"),
                ]
            elif "SELECT CASE" in query:
                self.one = (None,)

        def fetchone(self):
            return self.one

        def fetchall(self):
            return self.many

    provider = FakeConnectionProvider([])
    cursor = AttemptCursor()

    @contextmanager
    def attempt_cursor():
        yield cursor

    provider.cursor = attempt_cursor
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    attempt = database_helpers.start_or_resume_test_attempt("test-id", "student-id")

    answer_insert = next(
        query for query, _ in cursor.executed
        if "INSERT INTO attempt_answers" in query
    )
    question_list_query = next(
        query for query, _ in cursor.executed
        if "answer.selected_option_id" in query
    )
    assert "(attempt_id, question_id)" in answer_insert
    assert "question_order" not in answer_insert
    assert "ORDER BY answer.answer_attempt_id" in question_list_query
    assert attempt["questions"][0]["question_text"] == "Solve for x."


def test_submit_test_attempt_awards_correct_incorrect_and_unanswered_points(monkeypatch):
    class ScoringCursor:
        def __init__(self):
            self.one = None
            self.many = []
            self.executed = []

        def execute(self, query, parameters):
            self.executed.append((query, parameters))
            if "SELECT t.time_limit_minutes" in query:
                self.one = (None, "Algebra Check", False)
            elif "SELECT question_id, selected_option_id" in query:
                self.many = [
                    ("question-1", None),
                    ("question-2", None),
                    ("question-3", None),
                ]
            elif "SELECT is_correct" in query:
                self.one = (parameters[1] == "correct-option",)
            else:
                self.one = None

        def fetchone(self):
            return self.one

        def fetchall(self):
            return self.many

    provider = FakeConnectionProvider([])
    cursor = ScoringCursor()

    @contextmanager
    def scoring_cursor():
        yield cursor

    provider.cursor = scoring_cursor
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.submit_test_attempt(
        "test-1",
        "attempt-1",
        "student-1",
        {
            "question-1": "correct-option",
            "question-2": "incorrect-option",
        },
    )

    assert result == {
        "test_id": "test-1",
        "attempt_id": "attempt-1",
        "test_name": "Algebra Check",
        "question_count": 3,
        "correct_count": 1,
        "percentage": 100 / 3,
        "total_points": 20,
        "timed_out": False,
    }


def test_expired_test_does_not_accept_late_answers(monkeypatch):
    class ExpiredCursor:
        def __init__(self):
            self.one = None
            self.many = []

        def execute(self, query, parameters):
            if "SELECT t.time_limit_minutes" in query:
                self.one = (1, "Timed Test", True)
            elif "SELECT question_id, selected_option_id" in query:
                self.many = [("question-1", None)]
            elif "SELECT is_correct" in query:
                self.one = (parameters[1] == "correct-option",)
            else:
                self.one = None

        def fetchone(self):
            return self.one

        def fetchall(self):
            return self.many

    provider = FakeConnectionProvider([])
    cursor = ExpiredCursor()

    @contextmanager
    def expired_cursor():
        yield cursor

    provider.cursor = expired_cursor
    monkeypatch.setattr(database_helpers, "PostgresConnectionProvider", lambda: provider)

    result = database_helpers.submit_test_attempt(
        "test-1",
        "attempt-1",
        "student-1",
        {"question-1": "correct-option"},
    )

    assert result["total_points"] == 0
    assert result["correct_count"] == 0
    assert result["timed_out"] is True
