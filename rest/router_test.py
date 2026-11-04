# To Run: pytest rest/router_test.py

from types import SimpleNamespace

import pytest
from flask import g

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

    def test_root_route_redirects_to_login(self, client):
        # ACT
        response = client.get("/")

        # ASSERT
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    def test_login_route_renders(self, client):
        # ACT
        response = client.get("/login")

        # ASSERT
        assert response.status_code == 200
        assert b"Login" in response.data

    @pytest.mark.parametrize(
        ("role", "visible_item", "hidden_item"),
        [
            ("student", b"Assigned Tests", b"User Management"),
            ("lecturer", b"Manage Tests", b"Assigned Tests"),
            ("administrator", b"User Management", b"Assigned Tests"),
        ],
    )
    def test_sidebar_items_are_selected_by_user_role(self, role, visible_item, hidden_item):
        # ARRANGE
        app = create_app()

        @app.before_request
        def set_user_role():
            g.user = SimpleNamespace(role=role)

        # ACT
        response = app.test_client().get("/login")

        # ASSERT
        assert response.status_code == 200
        assert visible_item in response.data
        assert hidden_item not in response.data
