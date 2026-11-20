from datetime import datetime

from rest.student_dashboard import student_dashboard as dashboard_module

STUDENT_ID = "00000000-0000-4000-8000-000000000001"


def _log_in(client, role, user_id=STUDENT_ID):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


class TestStudentDashboardRoutes:
    def test_dashboard_shows_assigned_and_completed_tests_together(self, client, monkeypatch):
        requested_ids = []
        monkeypatch.setattr(
            dashboard_module,
            "get_assigned_tests",
            lambda student_id: requested_ids.append(student_id) or [
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
        _log_in(client, "student")

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert requested_ids == [STUDENT_ID]
        assert b"Algebra Check" in response.data
        assert b"Mathematics" in response.data
        assert b"Computing Basics" in response.data
        assert b"31 Oct 2026" in response.data
        assert b"80.0%" in response.data
        assert b"Assigned Tests" in response.data
        assert b"Completed Tests" in response.data
        assert b'href="/student-dashboard/"' in response.data

    def test_dashboard_shows_empty_states(self, client, monkeypatch):
        monkeypatch.setattr(dashboard_module, "get_assigned_tests", lambda student_id: [])
        monkeypatch.setattr(dashboard_module, "get_completed_tests", lambda student_id: [])
        _log_in(client, "student")

        response = client.get("/student-dashboard/")

        assert response.status_code == 200
        assert b"No tests to complete." in response.data
        assert b"No completed tests yet." in response.data

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