from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

from flask import g

from rest.student_dashboard import student_dashboard as dashboard_module
from rest.student_dashboard import testing as testing_module


class TestStudentDashboardRoutes:
    def test_dashboard_shows_assigned_and_completed_tests_together(self, client, monkeypatch):
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

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert b"Algebra Check" in response.data
        assert b"Mathematics" in response.data
        assert b"Computing Basics" in response.data
        assert b"31 Oct 2026" in response.data
        assert b"80.0%" in response.data
        assert b"Assigned Tests" in response.data
        assert b"Completed Tests" in response.data
        assert b'href="/student-dashboard/"' in response.data
        assert b'href="/student-dashboard/tests/00000000-0000-4000-8000-000000000042"' in response.data

    def test_test_lists_require_student_role(self, app, client):
        @app.before_request
        def set_lecturer():
            g.user = SimpleNamespace(role="lecturer", user_id="lecturer-id")

        response = client.get("/student-dashboard/")

        assert response.status_code == 403

    def test_missing_student_id_renders_empty_list_without_database_access(self, app, client):
        @app.before_request
        def set_student_without_id():
            g.user = SimpleNamespace(role="student")

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert b"No tests to complete" in response.data
        assert b"No completed tests yet" in response.data


class TestStudentTestingRoutes:
    def test_assigned_test_renders_question_counter_options_and_countdown(self, client, monkeypatch):
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
                    }
                ],
            },
        )

        response = client.get(f"/student-dashboard/tests/{test_id}")

        assert response.status_code == 200
        assert b"Algebra Check" in response.data
        assert b"Mathematics" in response.data
        assert b"Question <span data-current-question>1</span> of 1" in response.data
        assert b"What is 2 + 2?" in response.data
        assert b"data-countdown=\"299\"" in response.data
        assert b"4" in response.data
        assert b"5" in response.data

    def test_test_page_requires_a_student_account(self, app, client):
        app.config["TESTING"] = False

        response = client.get(
            "/student-dashboard/tests/00000000-0000-4000-8000-000000000001"
        )

        assert response.status_code == 403

    def test_submitting_test_records_form_answers_and_shows_result(self, client, monkeypatch):
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

    def test_expired_test_is_submitted_when_opened(self, client, monkeypatch):
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