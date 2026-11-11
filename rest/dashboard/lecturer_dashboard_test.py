# To Run: pytest rest/dashboard/lecturer_dashboard_test.py

from rest.dashboard.lecturer_dashboard import lecturer_dashboard_route


class TestLecturerDashboardRoute:
    """Test the lecturer_dashboard_route function"""

    def test_lecturer_dashboard_route_redirects_when_not_logged_in(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/dashboard/lecturer"):
            response = lecturer_dashboard_route()

        # ASSERT
        assert response.status_code == 302
        assert "/login" in response.location

    def test_lecturer_dashboard_route_redirects_for_wrong_role(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/dashboard/lecturer"):
            from flask import session

            session["user_id"] = "11111111-1111-1111-1111-111111111111"
            session["role"] = "student"
            response = lecturer_dashboard_route()

        # ASSERT
        assert response.status_code == 302
        assert "/login" in response.location

    def test_lecturer_dashboard_route_renders_for_logged_in_lecturer(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/dashboard/lecturer"):
            from flask import session

            session["user_id"] = "11111111-1111-1111-1111-111111111111"
            session["role"] = "lecturer"
            response = lecturer_dashboard_route()

        # ASSERT
        assert b"Lecturer Dashboard" in response.data
