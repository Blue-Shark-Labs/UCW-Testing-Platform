# To Run: pytest rest/home_test.py

from rest.home import home_route


class TestHomeRoute:
    """Test the home_route function"""

    def test_home_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/"):
            response = home_route()

        # ASSERT
        assert "Reinforcement Testing Platform" in response
