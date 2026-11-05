# To Run: pytest usecase/register_student_test.py

from dataclasses import replace
from unittest.mock import patch

from werkzeug.security import check_password_hash

from domain.entities.user import StudentRegistration
from usecase.register_student import register_student

VALID = StudentRegistration(
    first_name="Ada",
    last_name="Lovelace",
    email="ada@example.com",
    student_number="WS1234567",
    course_title="BSc DATS",
    password="SuperSecret1!",
)


class TestRegisterStudent:
    """Test the register_student function"""

    @patch("usecase.register_student.create_student")
    def test_stores_hashed_password_not_plain_text(self, mock_create_student):
        # ARRANGE
        mock_create_student.return_value = True

        # ACT
        errors = register_student(object(), VALID)

        # ASSERT
        assert errors == []
        password_hash = mock_create_student.call_args.args[2]
        assert password_hash != VALID.password
        assert check_password_hash(password_hash, VALID.password)

    @patch("usecase.register_student.create_student")
    def test_missing_fields_are_rejected(self, mock_create_student):
        # ARRANGE
        registration = replace(VALID, student_number="", first_name="", last_name="", course_title="", password="")

        # ACT
        errors = register_student(object(), registration)

        # ASSERT
        assert "Student number is required." in errors
        assert "First name is required." in errors
        assert "Last name is required." in errors
        assert "Course title is required." in errors
        assert "Password is required." in errors
        mock_create_student.assert_not_called()

    @patch("usecase.register_student.create_student")
    def test_short_password_is_rejected(self, mock_create_student):
        # ACT
        errors = register_student(object(), replace(VALID, password="short"))

        # ASSERT
        assert errors == ["Password must be at least 8 characters."]
        mock_create_student.assert_not_called()

    @patch("usecase.register_student.create_student")
    def test_duplicate_email_is_rejected(self, mock_create_student):
        # ARRANGE
        mock_create_student.return_value = False

        # ACT
        errors = register_student(object(), VALID)

        # ASSERT
        assert errors == ["An account with this email already exists."]
