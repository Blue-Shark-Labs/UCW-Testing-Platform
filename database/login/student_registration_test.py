# To Run: pytest database/login/student_registration_test.py

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from database.login.student_registration import (
    INSERT_STUDENT,
    STUDENT_NUMBER_CONSTRAINT,
    DuplicateStudentNumberError,
    StudentRegistration,
    create_student,
)

REGISTRATION = StudentRegistration(
    first_name="Ada",
    last_name="Lovelace",
    email="ada@example.com",
    student_number="S1234567",
    course_title="BSc Computer Science",
    password="SuperSecret1!",
)


class FakeConnectionProvider:
    """Stands in for PostgresConnectionProvider, returning a fixed row from the cursor."""

    def __init__(self, row):
        self.cursor_mock = MagicMock()
        self.cursor_mock.fetchone.return_value = row

    @contextmanager
    def cursor(self):
        yield self.cursor_mock


class TestCreateStudent:
    """Test the create_student function"""

    def test_inserts_unapproved_student_with_hash(self):
        # ARRANGE
        provider = FakeConnectionProvider(("user-id",))

        # ACT
        result = create_student(provider, REGISTRATION, "hashed-value")

        # ASSERT
        assert result is True
        user_params = provider.cursor_mock.execute.call_args_list[0].args[1]
        assert "hashed-value" in user_params
        assert REGISTRATION.password not in user_params
        provider.cursor_mock.execute.assert_called_with(
            INSERT_STUDENT, ("user-id", "S1234567", "BSc Computer Science")
        )
        assert "FALSE" in INSERT_STUDENT

    def test_returns_false_when_email_exists(self):
        # ARRANGE
        provider = FakeConnectionProvider(None)

        # ACT
        result = create_student(provider, REGISTRATION, "hashed-value")

        # ASSERT
        assert result is False
        assert provider.cursor_mock.execute.call_count == 1

    def test_raises_duplicate_student_number_error(self, monkeypatch):
        # ARRANGE
        class FakeUniqueViolation(Exception):
            diag = MagicMock(constraint_name=STUDENT_NUMBER_CONSTRAINT)

        monkeypatch.setattr("database.login.student_registration.UniqueViolation", FakeUniqueViolation)
        provider = FakeConnectionProvider(("user-id",))
        provider.cursor_mock.execute.side_effect = [None, FakeUniqueViolation()]

        # ACT / ASSERT
        with pytest.raises(DuplicateStudentNumberError):
            create_student(provider, REGISTRATION, "hashed-value")
