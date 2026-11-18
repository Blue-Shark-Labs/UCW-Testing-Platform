# To Run: pytest database/login/user_test.py

from contextlib import contextmanager
from unittest.mock import MagicMock

from database.login.user import clear_failed_logins, get_user_by_email, record_failed_login
from domain.entities.user import User


class FakeConnectionProvider:
    """Stands in for PostgresConnectionProvider, returning a fixed row from the cursor."""

    def __init__(self, row):
        self.cursor_mock = MagicMock()
        self.cursor_mock.fetchone.return_value = row

    @contextmanager
    def cursor(self):
        yield self.cursor_mock


class TestGetUserByEmail:
    """Test the get_user_by_email function"""

    def test_get_user_by_email_maps_row_to_entity(self):
        # ARRANGE
        row = ("11111111-1111-1111-1111-111111111111", "student@example.com", "hashed-password", "student", False, True)
        connection_provider = FakeConnectionProvider(row)

        # ACT
        result = get_user_by_email(connection_provider, "student@example.com")

        # ASSERT
        assert result == User(
            user_id="11111111-1111-1111-1111-111111111111",
            email="student@example.com",
            password_hash="hashed-password",
            role="student",
            is_disabled=False,
            is_locked=True,
        )
        connection_provider.cursor_mock.execute.assert_called_once()

    def test_get_user_by_email_returns_none_when_not_found(self):
        # ARRANGE
        connection_provider = FakeConnectionProvider(None)

        # ACT
        result = get_user_by_email(connection_provider, "missing@example.com")

        # ASSERT
        assert result is None


class TestRecordFailedLogin:
    """Test the record_failed_login function"""

    def test_record_failed_login_passes_limits_to_query(self):
        # ARRANGE
        connection_provider = FakeConnectionProvider(None)

        # ACT
        record_failed_login(connection_provider, "user-1", 10, 15)

        # ASSERT
        _, params = connection_provider.cursor_mock.execute.call_args.args
        assert params == {"user_id": "user-1", "max_attempts": 10, "lockout_minutes": 15}


class TestClearFailedLogins:
    """Test the clear_failed_logins function"""

    def test_clear_failed_logins_targets_user(self):
        # ARRANGE
        connection_provider = FakeConnectionProvider(None)

        # ACT
        clear_failed_logins(connection_provider, "user-1")

        # ASSERT
        _, params = connection_provider.cursor_mock.execute.call_args.args
        assert params == ("user-1",)
