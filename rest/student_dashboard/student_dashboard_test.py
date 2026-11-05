from datetime import datetime
from types import SimpleNamespace

from flask import g

from rest.student_dashboard import student_dashboard as dashboard_module


class TestStudentDashboardRoutes:
    def test_dashboard_shows_assigned_and_completed_tests_together(self, client, monkeypatch):
        monkeypatch.setattr(
            dashboard_module,
            "get_assigned_tests",
            lambda student_id: [
                {"test_name": "Algebra Check", "subject_name": "Mathematics", "question_count": 12}
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