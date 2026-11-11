# To Run: pytest usecase/authenticate_user_test.py

from unittest.mock import patch

from domain.entities.user import User
from usecase.authenticate_user import authenticate_user


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


class TestAuthenticateUser:
    """Test the authenticate_user function"""

    @patch("usecase.authenticate_user.check_password_hash")
    @patch("usecase.authenticate_user.get_user_by_email")
    def test_authenticate_user_returns_user_for_valid_credentials(
        self, mock_get_user_by_email, mock_check_password_hash
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

    @patch("usecase.authenticate_user.get_user_by_email")
    def test_authenticate_user_returns_none_when_user_not_found(self, mock_get_user_by_email):
        # ARRANGE
        mock_get_user_by_email.return_value = None

        # ACT
        result = authenticate_user(object(), "missing@example.com", "password")

        # ASSERT
        assert result is None

    @patch("usecase.authenticate_user.check_password_hash")
    @patch("usecase.authenticate_user.get_user_by_email")
    def test_authenticate_user_returns_none_when_account_disabled(
        self, mock_get_user_by_email, mock_check_password_hash
    ):
        # ARRANGE
        user = make_user(is_disabled=True)
        mock_get_user_by_email.return_value = user

        # ACT
        result = authenticate_user(object(), "student@example.com", "correct-password")

        # ASSERT
        assert result is None
        mock_check_password_hash.assert_not_called()

    @patch("usecase.authenticate_user.check_password_hash")
    @patch("usecase.authenticate_user.get_user_by_email")
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

    @patch("usecase.authenticate_user.check_password_hash")
    @patch("usecase.authenticate_user.get_user_by_email")
    def test_authenticate_user_returns_none_for_incorrect_password(
        self, mock_get_user_by_email, mock_check_password_hash
    ):
        # ARRANGE
        user = make_user()
        mock_get_user_by_email.return_value = user
        mock_check_password_hash.return_value = False

        # ACT
        result = authenticate_user(object(), "student@example.com", "wrong-password")

        # ASSERT
        assert result is None
