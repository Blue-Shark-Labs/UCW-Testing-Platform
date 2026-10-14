# To Run: pytest rest/router_test.py

from rest.router import create_app


class TestCreateApp:
    """Test the create_app function"""

    def test_create_app_returns_flask_app(self):
        # ACT
        app = create_app()

        # ASSERT
        assert app is not None

    def test_home_route_registered(self):
        # ARRANGE
        app = create_app()

        # ACT
        rules = {rule.rule for rule in app.url_map.iter_rules()}

        # ASSERT
        assert "/" in rules
