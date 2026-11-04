# To Run: pytest rest/login/register_test.py

from unittest.mock import patch

from rest.login.register import register_route

VALID_FORM = {
    "student_number": "S1234567",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "course_title": "BSc Computer Science",
    "password": "SuperSecret1!",
}


class TestRegisterRoute:
    """Test the register_route function"""

    def test_register_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/register"):
            response = register_route()

        # ASSERT
        assert "Sign Up" in response

    def test_register_form_prompts_for_required_fields(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/register"):
            response = register_route()

        # ASSERT
        for field in ("student_number", "first_name", "last_name", "course_title", "password"):
            assert f'name="{field}"' in response

    @patch("rest.login.register.PostgresConnectionProvider")
    @patch("rest.login.register.register_student")
    def test_successful_registration_shows_pending_approval(self, mock_register_student, mock_provider, app):
        # ARRANGE
        mock_register_student.return_value = []

        # ACT
        with app.test_request_context("/register", method="POST", data=VALID_FORM):
            response = register_route()

        # ASSERT
        assert "awaiting lecturer approval" in response
        registration = mock_register_student.call_args.args[1]
        assert registration.student_number == "S1234567"

    @patch("rest.login.register.PostgresConnectionProvider")
    @patch("rest.login.register.register_student")
    def test_failed_registration_shows_errors_without_password(self, mock_register_student, mock_provider, app):
        # ARRANGE
        mock_register_student.return_value = ["Course title is required."]

        # ACT
        with app.test_request_context("/register", method="POST", data=VALID_FORM):
            body, status = register_route()

        # ASSERT
        assert status == 400
        assert "Course title is required." in body
        assert VALID_FORM["password"] not in body
