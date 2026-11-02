# To Run: pytest rest/login_test.py

from rest.login.login import login_route


class TestLoginRoute:
    """Test the login_route function"""

    def test_login_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/"):
            response = login_route()

        # ASSERT
        assert "Login" in response
