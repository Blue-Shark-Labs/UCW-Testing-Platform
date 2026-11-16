# To Run: pytest rest/login/login_test.py

from unittest.mock import patch

from domain.entities.user import User
from rest.login.login import login_route


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
