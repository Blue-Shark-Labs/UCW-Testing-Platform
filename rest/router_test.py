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

    def test_root_route_serves_landing_page(self):
        # ARRANGE
        app = create_app()

        # ACT
        endpoint, _ = app.url_map.bind("localhost").match("/")

        # ASSERT
        assert endpoint == "landing_page.landing_page_route"

    def test_login_route_renders(self, client):
        # ACT
        response = client.get("/login")

        # ASSERT
        assert response.status_code == 200
        assert b'name="email"' in response.data
        assert b'name="password"' in response.data

    @pytest.mark.parametrize(
        ("role", "page_path", "visible_item", "hidden_item"),
        [
            ("student", "/dashboard/student", b"Assigned Tests", b"User Management"),
            ("lecturer", "/dashboard/lecturer", b"Test Management", b"Assigned Tests"),
            ("admin", "/administrator/create-user", b"User Management", b"Assigned Tests"),
            ("student", "/dashboard/student", b"Assigned Tests", b">Home<"),
        ],
    )
    
    def test_sidebar_items_are_selected_by_session_role(
        self, client, monkeypatch, role, page_path, visible_item, hidden_item
    ):
        # ARRANGE
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return ("Test", "User", role)

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)

        with client.session_transaction() as sess:
            sess["user_id"] = "11111111-1111-1111-1111-111111111111"
            sess["role"] = role

        # ACT
        # Use a page available to each role that renders the sidebar layout.
        response = client.get(page_path)

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
