# To Run: pytest rest/register_test.py

from rest.register import register_route


class TestRegisterRoute:
    """Test the register_route function"""

    def test_register_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/register"):
            response = register_route()

        # ASSERT
        assert "Sign Up" in response
