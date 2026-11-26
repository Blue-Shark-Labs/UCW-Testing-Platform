# To Run: pytest rest/login/login_test.py

from unittest.mock import patch

import pytest

from database.login.user import User
from rest.login.login import (
    LOCKOUT_MINUTES,
    MAX_FAILED_ATTEMPTS,
    AccountLockedError,
    authenticate_user,
    login_route,
)


def make_user(**overrides):
    defaults = dict(
        user_id="11111111-1111-1111-1111-111111111111",
        email="student@example.com",
        password_hash="hashed-password",
        role="student",
        is_disabled=False,
    )
    defaults.update(overrides)
    return User(**defaults)


class TestLoginRoute:
    """Test the login_route function"""

    def test_login_route_renders_form_on_get(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/login"):
            response = login_route()

        # ASSERT
        assert 'name="email"' in response
        assert 'name="password"' in response
        assert "Blue Shark Labs logo" in response

    @patch("rest.login.login.PostgresConnectionProvider")
    @patch("rest.login.login.authenticate_user")
    def test_login_route_redirects_to_role_dashboard_on_success(
        self, mock_authenticate_user, mock_connection_provider, app
    ):
        # ARRANGE
        mock_authenticate_user.return_value = make_user(role="lecturer")

        # ACT
        with app.test_request_context(
            "/login", method="POST", data={"email": "lecturer@example.com", "password": "correct-password"}
        ):
            response = login_route()

        # ASSERT
        assert response.status_code == 302
        assert "/dashboard/lecturer" in response.location

    @patch("rest.login.login.PostgresConnectionProvider")
    @patch("rest.login.login.authenticate_user")
    def test_admin_login_redirects_to_administrator_subjects(
        self, mock_authenticate_user, mock_connection_provider, app
    ):
        mock_authenticate_user.return_value = make_user(role="admin")

        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": "admin@example.com", "password": "correct-password"},
        ):
            response = login_route()

        assert response.status_code == 302
        assert response.location == "/administrator/subjects"

    @patch("rest.login.login.PostgresConnectionProvider")
    @patch("rest.login.login.authenticate_user")
    def test_login_route_shows_error_for_invalid_or_disabled_account(
        self, mock_authenticate_user, mock_connection_provider, app
    ):
        # ARRANGE
        mock_authenticate_user.return_value = None

        # ACT
        with app.test_request_context(
            "/login", method="POST", data={"email": "student@example.com", "password": "wrong-password"}
        ):
            response = login_route()

        # ASSERT
        assert "Incorrect email or password" in response
        assert "Accounts are locked for 15 minutes after 10 failed attempts." in response

    @patch("rest.login.login.PostgresConnectionProvider")
    @patch("rest.login.login.authenticate_user")
    def test_login_route_shows_lockout_message_when_account_locked(
        self, mock_authenticate_user, mock_connection_provider, app
    ):
        # ARRANGE
        mock_authenticate_user.side_effect = AccountLockedError()

        # ACT
        with app.test_request_context(
            "/login", method="POST", data={"email": "student@example.com", "password": "any-password"}
        ):
            body, status_code = login_route()

        # ASSERT
        assert status_code == 429
        assert "Please try again in 15 minutes." in body

    @patch("rest.login.login.PostgresConnectionProvider")
    @patch("rest.login.login.authenticate_user")
    def test_login_route_redirects_to_mfa_challenge_without_signing_in(
        self, mock_authenticate_user, mock_connection_provider, client
    ):
        # ARRANGE
        mock_authenticate_user.return_value = make_user(role="lecturer", mfa_enabled=True)

        # ACT
        response = client.post("/login", data={"email": "lecturer@example.com", "password": "correct-password"})

        # ASSERT
        assert response.status_code == 302
        assert response.location == "/login/mfa"
        with client.session_transaction() as sess:
            assert "user_id" not in sess
            assert sess["mfa_pending_user_id"] == "11111111-1111-1111-1111-111111111111"


class TestAuthenticateUser:
    """Test the authenticate_user function"""

    @patch("rest.login.login.clear_failed_logins")
    @patch("rest.login.login.check_password_hash")
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_returns_user_for_valid_credentials(
        self, mock_get_user_by_email, mock_check_password_hash, mock_clear_failed_logins
    ):
        # ARRANGE
        user = make_user()
        mock_get_user_by_email.return_value = user
        mock_check_password_hash.return_value = True
        connection_provider = object()

        # ACT
        result = authenticate_user(connection_provider, "student@example.com", "correct-password")

        # ASSERT
        assert result is user
        mock_check_password_hash.assert_called_once_with(user.password_hash, "correct-password")
        mock_clear_failed_logins.assert_called_once_with(connection_provider, user.user_id)

    @patch("rest.login.login.clear_failed_logins")
    @patch("rest.login.login.check_password_hash", return_value=True)
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_keeps_failure_count_until_mfa_code_verified(
        self, mock_get_user_by_email, _mock_check_password_hash, mock_clear_failed_logins
    ):
        # ARRANGE
        mock_get_user_by_email.return_value = make_user(mfa_enabled=True)

        # ACT
        result = authenticate_user(object(), "student@example.com", "correct-password")

        # ASSERT
        assert result.mfa_enabled
        mock_clear_failed_logins.assert_not_called()

    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_returns_none_when_user_not_found(self, mock_get_user_by_email):
        # ARRANGE
        mock_get_user_by_email.return_value = None

        # ACT
        result = authenticate_user(object(), "missing@example.com", "password")

        # ASSERT
        assert result is None

    @patch("rest.login.login.check_password_hash")
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_returns_none_when_account_disabled(
        self, mock_get_user_by_email, mock_check_password_hash
    ):
        # ARRANGE
        mock_get_user_by_email.return_value = make_user(is_disabled=True)

        # ACT
        result = authenticate_user(object(), "student@example.com", "correct-password")

        # ASSERT
        assert result is None
        mock_check_password_hash.assert_not_called()

    @patch("rest.login.login.check_password_hash")
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_returns_none_when_student_not_approved(
        self, mock_get_user_by_email, mock_check_password_hash
    ):
        # ARRANGE
        mock_get_user_by_email.return_value = make_user(is_approved=False)

        # ACT
        result = authenticate_user(object(), "student@example.com", "correct-password")

        # ASSERT
        assert result is None
        mock_check_password_hash.assert_not_called()

    @patch("rest.login.login.record_failed_login")
    @patch("rest.login.login.check_password_hash")
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_returns_none_for_incorrect_password(
        self, mock_get_user_by_email, mock_check_password_hash, mock_record_failed_login
    ):
        # ARRANGE
        user = make_user()
        mock_get_user_by_email.return_value = user
        mock_check_password_hash.return_value = False
        connection_provider = object()

        # ACT
        result = authenticate_user(connection_provider, "student@example.com", "wrong-password")

        # ASSERT
        assert result is None
        mock_record_failed_login.assert_called_once_with(
            connection_provider, user.user_id, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES
        )

    @patch("rest.login.login.check_password_hash")
    @patch("rest.login.login.get_user_by_email")
    def test_authenticate_user_raises_when_account_locked(
        self, mock_get_user_by_email, mock_check_password_hash
    ):
        # ARRANGE
        mock_get_user_by_email.return_value = make_user(is_locked=True)

        # ACT / ASSERT
        with pytest.raises(AccountLockedError):
            authenticate_user(object(), "student@example.com", "correct-password")
        mock_check_password_hash.assert_not_called()
