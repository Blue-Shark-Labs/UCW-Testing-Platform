# To Run: pytest rest/dashboard/student_dashboard_test.py

from rest.dashboard.student_dashboard import student_dashboard_route


class TestStudentDashboardRoute:
    """Test the student_dashboard_route function"""

    def test_student_dashboard_route_redirects_when_not_logged_in(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/dashboard/student"):
            response = student_dashboard_route()

        # ASSERT
        assert response.status_code == 302
        assert "/login" in response.location

    def test_student_dashboard_route_renders_for_logged_in_student(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/dashboard/student"):
            from flask import session

            session["user_id"] = "11111111-1111-1111-1111-111111111111"
            session["role"] = "student"
            response = student_dashboard_route()

        # ASSERT
        assert "Student Dashboard" in response
