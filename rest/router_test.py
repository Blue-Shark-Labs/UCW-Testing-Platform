# To Run: pytest rest/router_test.py

import pytest

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

    def test_root_route_redirects_to_landing_page(self, client):
        # ACT
        response = client.get("/")

        # ASSERT
        assert response.status_code == 302
        assert response.headers["Location"] == "/landing-page/"

    def test_login_route_renders(self, client):
        # ACT
        response = client.get("/login")

        # ASSERT
        assert response.status_code == 200
        assert b'name="email"' in response.data
        assert b'name="password"' in response.data

    def test_create_app_fails_without_secret_key(self, monkeypatch):
        # ARRANGE
        monkeypatch.delenv("SECRET_KEY", raising=False)

        # ACT / ASSERT
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app()
