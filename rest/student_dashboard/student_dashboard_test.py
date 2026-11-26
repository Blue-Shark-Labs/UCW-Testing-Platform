import re
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

import pytest

from rest.student_dashboard import student_dashboard as dashboard_module
from rest.student_dashboard import testing as testing_module

STUDENT_ID = "00000000-0000-4000-8000-000000000001"


@pytest.fixture(autouse=True)
def stub_session_user_db(monkeypatch):
    """Prevent load_session_user() in rest/router.py from hitting PostgreSQL during unit tests."""
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return ("Test", "Student", "student")

    class FakeConnectionProvider:
        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)


def _log_in(client, role, user_id=STUDENT_ID):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


class TestStudentDashboardRoutes:
    def test_dashboard_requires_student_login(self, client):
        response = client.get("/student-dashboard/")

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    def test_dashboard_shows_assigned_and_completed_tests_together(self, client, monkeypatch):
        submitted_for = []
        monkeypatch.setattr(
            dashboard_module,
            "submit_expired_test_attempts",
            submitted_for.append,
        )
        monkeypatch.setattr(
            dashboard_module,
            "get_assigned_tests",
            lambda student_id: [
                {
                    "test_id": "00000000-0000-4000-8000-000000000042",
                    "test_name": "Algebra Check",
                    "subject_name": "Mathematics",
                    "question_count": 12,
                }
            ],
        )
        monkeypatch.setattr(
            dashboard_module,
            "get_completed_tests",
            lambda student_id: [
                {
                    "test_name": "Computing Basics",
                    "completed_at": datetime(2026, 10, 31, 14, 30),
                    "question_count": 5,
                    "percentage": 80.0,
                    "total_points": 110,
                }
            ],
        )
        _log_in(client, "student")

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert len(submitted_for) == 1
        assert b"Algebra Check" in response.data
        assert b"Mathematics" in response.data
        assert b"Computing Basics" in response.data
        assert b"31 Oct 2026" in response.data
        assert b"80.0%" in response.data
        assert b"Skip to main content" in response.data
        assert b"id=\"student-page-main\"" in response.data
        assert b"<nav aria-label=\"Primary\"" in response.data
        assert b"role=\"region\" aria-label=\"Assigned tests\" tabindex=\"0\"" in response.data
        assert b"role=\"region\" aria-label=\"Completed tests\" tabindex=\"0\"" in response.data
        assert b"<title>Tests | Reinforcement Testing Platform</title>" in response.data
        assert b"<h1 id=\"student-page-main\" tabindex=\"-1\"" in response.data
        assert b">Tests</h1>" in response.data
        assert b"Assigned Tests" in response.data
        assert b"Completed Tests" in response.data
        assert b'href="/student-dashboard/"' in response.data
        assert b'href="/student-dashboard/tests/00000000-0000-4000-8000-000000000042"' in response.data

    def test_dashboard_shows_empty_states(self, client, monkeypatch):
        monkeypatch.setattr(dashboard_module, "submit_expired_test_attempts", lambda student_id: None)
        monkeypatch.setattr(dashboard_module, "get_assigned_tests", lambda student_id: [])
        monkeypatch.setattr(dashboard_module, "get_completed_tests", lambda student_id: [])
        _log_in(client, "student")

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert b"No tests to complete" in response.data
        assert b"No completed tests yet" in response.data


class TestStudentTestingRoutes:
    def test_assigned_test_renders_question_counter_options_and_countdown(self, client, monkeypatch):
        _log_in(client, "student")
        test_id = UUID("00000000-0000-4000-8000-000000000001")
        attempt_id = UUID("00000000-0000-4000-8000-000000000005")
        question_id = UUID("00000000-0000-4000-8000-000000000002")
        option_id = UUID("00000000-0000-4000-8000-000000000003")
        monkeypatch.setattr(
            testing_module,
            "start_or_resume_test_attempt",
            lambda test_id, student_id: {
                "attempt_id": attempt_id,
                "test_id": test_id,
                "test_name": "Algebra Check",
                "subject_name": "Mathematics",
                "time_limit_minutes": 5,
                "seconds_remaining": 299,
                "questions": [
                    {
                        "question_id": question_id,
                        "question_text": "What is 2 + 2?",
                        "selected_option_id": None,
                        "options": [
                            {"option_id": option_id, "option_text": "4"},
                            {"option_id": UUID("00000000-0000-4000-8000-000000000004"), "option_text": "5"},
                        ],
                    },
                    {
                        "question_id": UUID("00000000-0000-4000-8000-000000000006"),
                        "question_text": "What is 3 + 3?",
                        "selected_option_id": None,
                        "options": [
                            {
                                "option_id": UUID("00000000-0000-4000-8000-000000000007"),
                                "option_text": "6",
                            },
                            {
                                "option_id": UUID("00000000-0000-4000-8000-000000000008"),
                                "option_text": "7",
                            },
                        ],
                    },
                ],
            },
        )

        response = client.get(f"/student-dashboard/tests/{test_id}")

        assert response.status_code == 200
        assert b"Algebra Check" in response.data
        assert b"Mathematics" in response.data
        assert b"Question <span data-current-question>1</span> of 2" in response.data
        assert b"What is 2 + 2?" in response.data
        assert b"data-countdown=\"299\"" in response.data
        assert b"aria-labelledby=\"countdown-label\"" in response.data
        assert b"data-countdown-announcement role=\"status\"" in response.data
        assert b"<legend class=\"sr-only\">What is 2 + 2? Choose one answer</legend>" in response.data
        assert b"<legend class=\"sr-only\">What is 3 + 3? Choose one answer</legend>" in response.data
        assert b'id="question-panel-00000000-0000-4000-8000-000000000006"' in response.data
        assert re.search(rb'data-question-index="1"\s+hidden', response.data)
        assert b'id="answer-00000000-0000-4000-8000-000000000006-00000000-0000-4000-8000-000000000007"' in response.data
        assert b'for="answer-00000000-0000-4000-8000-000000000006-00000000-0000-4000-8000-000000000007"' in response.data
        assert b"What is 3 + 3?" in response.data
        assert b"<span>6</span>" in response.data
        assert b"4" in response.data
        assert b"5" in response.data

    def test_test_page_requires_a_student_account(self, app, client):
        app.config["TESTING"] = False

        response = client.get(
            "/student-dashboard/tests/00000000-0000-4000-8000-000000000001"
        )

        assert response.status_code == 403

    def test_submitting_test_records_form_answers_and_shows_result(self, client, monkeypatch):
        _log_in(client, "student")
        test_id = UUID("00000000-0000-4000-8000-000000000001")
        attempt_id = UUID("00000000-0000-4000-8000-000000000002")
        question_id = UUID("00000000-0000-4000-8000-000000000003")
        option_id = UUID("00000000-0000-4000-8000-000000000004")
        submitted = {}

        def fake_submit(test_id, attempt_id, student_id, answers):
            submitted.update(
                test_id=test_id,
                attempt_id=attempt_id,
                student_id=student_id,
                answers=answers,
            )
            return {
                "test_name": "Algebra Check",
                "question_count": 1,
                "correct_count": 1,
                "percentage": 100.0,
                "total_points": 30,
                "timed_out": False,
            }

        monkeypatch.setattr(testing_module, "submit_test_attempt", fake_submit)

        response = client.post(
            f"/student-dashboard/tests/{test_id}/attempts/{attempt_id}/submit",
            data={f"answer_{question_id}": str(option_id)},
        )

        assert response.status_code == 200
        assert b"Test submitted" in response.data
        assert b"30" in response.data
        assert submitted["answers"] == {str(question_id): option_id}
        assert submitted["student_id"] == "00000000-0000-4000-8000-000000000001"

    def test_submitting_with_unanswered_questions_shows_error(self, client, monkeypatch):
        _log_in(client, "student")
        test_id = UUID("00000000-0000-4000-8000-000000000001")
        attempt_id = UUID("00000000-0000-4000-8000-000000000002")
        first_question = UUID("00000000-0000-4000-8000-000000000003")
        second_question = UUID("00000000-0000-4000-8000-000000000004")

        def fake_submit(test_id, attempt_id, student_id, answers):
            raise testing_module.UnansweredQuestionsError([second_question])

        monkeypatch.setattr(testing_module, "submit_test_attempt", fake_submit)
        monkeypatch.setattr(
            testing_module,
            "start_or_resume_test_attempt",
            lambda test_id, student_id: {
                "attempt_id": attempt_id,
                "test_id": test_id,
                "test_name": "Algebra Check",
                "subject_name": "Mathematics",
                "time_limit_minutes": None,
                "seconds_remaining": None,
                "questions": [
                    {"question_id": first_question, "question_text": "Q1", "selected_option_id": None, "options": []},
                    {"question_id": second_question, "question_text": "Q2", "selected_option_id": None, "options": []},
                ],
            },
        )

        response = client.post(
            f"/student-dashboard/tests/{test_id}/attempts/{attempt_id}/submit",
            data={},
        )

        assert response.status_code == 400
        assert b"Answer every question before submitting. Unanswered: 2." in response.data

    def test_expired_test_is_submitted_when_opened(self, client, monkeypatch):
        _log_in(client, "student")
        test_id = UUID("00000000-0000-4000-8000-000000000001")
        monkeypatch.setattr(
            testing_module,
            "start_or_resume_test_attempt",
            lambda test_id, student_id: {
                "attempt_id": "attempt-1",
                "test_id": test_id,
                "test_name": "Timed Algebra",
                "subject_name": "Mathematics",
                "time_limit_minutes": 1,
                "seconds_remaining": 0,
                "questions": [],
            },
        )
        submitted = []

        def fake_submit(test_id, attempt_id, student_id):
            submitted.append((test_id, attempt_id, student_id))
            return {
                "test_name": "Timed Algebra",
                "question_count": 1,
                "correct_count": 0,
                "percentage": 0.0,
                "total_points": 0,
                "timed_out": True,
            }

        monkeypatch.setattr(testing_module, "submit_test_attempt", fake_submit)

        response = client.get(f"/student-dashboard/tests/{test_id}")

        assert response.status_code == 200
        assert b"time limit expired" in response.data.lower()
        assert submitted[0][1] == "attempt-1"

    def test_test_lists_require_student_role(self, client, monkeypatch):
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return ("Test", "Lecturer", "lecturer")

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr(
            "rest.router.PostgresConnectionProvider", FakeConnectionProvider
        )
        _log_in(client, "lecturer", user_id=STUDENT_ID)

        response = client.get("/student-dashboard/")

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    def test_unauthenticated_user_is_redirected_to_login(self, client):
        response = client.get("/student-dashboard/")

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"
