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

    @pytest.mark.parametrize(
        ("role", "visible_item", "hidden_item"),
        [
            ("student", b"Assigned Tests", b"User Management"),
            ("lecturer", b"Manage Tests", b"Assigned Tests"),
            ("admin", b"User Management", b"Assigned Tests"),
        ],
    )
    def test_sidebar_items_are_selected_by_session_role(self, client, role, visible_item, hidden_item):
        # ARRANGE
        with client.session_transaction() as session:
            session["user_id"] = "11111111-1111-1111-1111-111111111111"
            session["role"] = role

        # ACT
        # Login is a standalone guest page, so use a page that renders the sidebar layout.
        response = client.get("/pr-block/")

        # ASSERT
        assert response.status_code == 200
        assert visible_item in response.data
        assert hidden_item not in response.data

    def test_session_cookie_is_secure_by_default(self, monkeypatch):
        # ARRANGE
        monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)

        # ACT
        app = create_app()

        # ASSERT
        assert app.config["SESSION_COOKIE_SECURE"] is True

    def test_session_cookie_secure_can_be_disabled_for_local_dev(self, monkeypatch):
        # ARRANGE
        monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")

        # ACT
        app = create_app()

        # ASSERT
        assert app.config["SESSION_COOKIE_SECURE"] is False

    def test_create_app_fails_without_secret_key(self, monkeypatch):
        # ARRANGE
        monkeypatch.delenv("SECRET_KEY", raising=False)

        # ACT / ASSERT
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app()
