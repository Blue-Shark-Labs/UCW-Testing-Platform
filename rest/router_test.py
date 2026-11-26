# To Run: pytest rest/router_test.py

import re

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
            ("student", "/dashboard/student", b"Tests", b"User Management"),
            ("lecturer", "/dashboard/lecturer", b"Quiz Management", b"<span>Tests</span>"),
            ("admin", "/administrator/users", b"User Management", b"<span>Tests</span>"),
            ("student", "/dashboard/student", b"Subject Leaderboards", b"Quiz Management"),
        ],
    )
    
    def test_sidebar_items_are_selected_by_session_role(
        self, client, monkeypatch, role, page_path, visible_item, hidden_item
    ):
        # ARRANGE
        class FakeCursor:
            query = ""

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                self.query = query.lower()

            def fetchone(self):
                if "count(*)" in self.query:
                    return (0,)
                return ("Test", "User", role)

            def fetchall(self):
                return []

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)
        monkeypatch.setattr(
            "database.administrator.users.PostgresConnectionProvider",
            FakeConnectionProvider,
        )
        monkeypatch.setattr("rest.student_dashboard.student_dashboard.get_assigned_tests", lambda student_id: [])
        monkeypatch.setattr("rest.student_dashboard.student_dashboard.get_completed_tests", lambda student_id: [])

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
        assert b'href="/privacy"' in response.data
        assert b">Privacy</span>" in response.data

    def test_privacy_policy_route_renders(self, client):
        response = client.get("/privacy")

        assert response.status_code == 200
        assert b"Privacy Policy" in response.data
        assert b"Information We Collect" in response.data
        assert b"Main Menu" not in response.data
        assert b'href="/"' in response.data

    def test_sidebar_supported_items_are_full_row_links(
        self, client, monkeypatch
    ):
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return ("Test", "User", "student")

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr(
            "rest.router.PostgresConnectionProvider",
            FakeConnectionProvider,
        )
        with client.session_transaction() as sess:
            sess["user_id"] = "11111111-1111-1111-1111-111111111111"
            sess["role"] = "student"

        response = client.get("/pr-block/")

        assert response.status_code == 200
        assert re.search(
            rb'<a\s+href="/student-dashboard/"\s+class="[^"]*"[^>]*>'
            rb'.*?<svg[^>]*>.*?</svg>.*?Tests</span>.*?</a>',
            response.data,
            re.DOTALL,
        )
        assert re.search(
            rb'<a\s+href="/pr-block/"\s+class="[^"]*"[^>]*>'
            rb'.*?<svg[^>]*>.*?</svg>.*?Home</span>.*?</a>',
            response.data,
            re.DOTALL,
        )
        assert b'href="#"' not in response.data
        assert re.search(
            rb'<a\s+href="/leaderboards"\s+class="[^"]*"[^>]*>'
            rb'.*?<svg[^>]*>.*?</svg>.*?Subject Leaderboards</span>.*?</a>',
            response.data,
            re.DOTALL,
        )

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
