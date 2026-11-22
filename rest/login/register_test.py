# To Run: pytest rest/login/register_test.py

from dataclasses import replace
from unittest.mock import patch

from werkzeug.security import check_password_hash

from database.login.student_registration import DuplicateStudentNumberError, StudentRegistration
from rest.login.register import register_route, register_student

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


VALID_REGISTRATION = StudentRegistration(
    first_name="Ada",
    last_name="Lovelace",
    email="ada@example.com",
    student_number="WS1234567",
    course_title="BSc DATS",
    password="SuperSecret1!",
)


class TestRegisterStudent:
    """Test the register_student function"""

    @patch("rest.login.register.create_student")
    def test_stores_hashed_password_not_plain_text(self, mock_create_student):
        # ARRANGE
        mock_create_student.return_value = True

        # ACT
        errors = register_student(object(), VALID_REGISTRATION)

        # ASSERT
        assert errors == []
        password_hash = mock_create_student.call_args.args[2]
        assert password_hash != VALID_REGISTRATION.password
        assert check_password_hash(password_hash, VALID_REGISTRATION.password)

    @patch("rest.login.register.create_student")
    def test_missing_fields_are_rejected(self, mock_create_student):
        # ARRANGE
        registration = replace(
            VALID_REGISTRATION, student_number="", first_name="", last_name="", course_title="", password=""
        )

        # ACT
        errors = register_student(object(), registration)

        # ASSERT
        assert "Student number is required." in errors
        assert "First name is required." in errors
        assert "Last name is required." in errors
        assert "Course title is required." in errors
        assert "Password is required." in errors
        mock_create_student.assert_not_called()

    @patch("rest.login.register.create_student")
    def test_short_password_is_rejected(self, mock_create_student):
        # ACT
        errors = register_student(object(), replace(VALID_REGISTRATION, password="short"))

        # ASSERT
        assert errors == ["Password must be at least 8 characters."]
        mock_create_student.assert_not_called()

    @patch("rest.login.register.create_student")
    def test_duplicate_email_is_rejected(self, mock_create_student):
        # ARRANGE
        mock_create_student.return_value = False

        # ACT
        errors = register_student(object(), VALID_REGISTRATION)

        # ASSERT
        assert errors == ["An account with this email already exists."]

    @patch("rest.login.register.create_student")
    def test_duplicate_student_number_is_rejected(self, mock_create_student):
        # ARRANGE
        mock_create_student.side_effect = DuplicateStudentNumberError()

        # ACT
        errors = register_student(object(), VALID_REGISTRATION)

        # ASSERT
        assert errors == ["An account with this student number already exists."]
