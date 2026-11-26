# To Run: pytest rest/landing_page/landing_page_test.py

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask import g

from database.landing_page.company_info import CompanyInfo
from rest.landing_page.landing_page import landing_page_route
from rest.privacy_policy import privacy_policy_route


class TestLandingPageRoute:
    """Test the landing_page_route function"""

    @patch("rest.landing_page.landing_page.PostgresConnectionProvider")
    @patch("rest.landing_page.landing_page.get_company_info")
    def test_landing_page_route_renders(self, mock_get_company_info, mock_connection_provider, app):
        # ARRANGE
        mock_get_company_info.return_value = CompanyInfo(
            product_name="Reinforcement Testing Platform",
            product_description="An adaptive testing platform.",
            contact_email="contact@bluesharklabs.com",
            contact_phone="+44 1234 567890",
            contact_address="Blue Shark Labs, Weston-super-Mare, UK",
        )

        # ACT
        with app.test_request_context("/"):
            response = landing_page_route()

        # ASSERT
        assert "Landing Page" in response
        assert 'href="/privacy"' in response
        assert "Guest" in response
        assert "Log In" in response
        assert "Sign Up" in response
        mock_get_company_info.assert_called_once_with(mock_connection_provider.return_value)

    @pytest.mark.parametrize(
        ("role", "app_url"),
        [
            ("student", "/pr-block/"),
            ("lecturer", "/dashboard/lecturer"),
            ("admin", "/administrator/subjects"),
        ],
    )
    @patch("rest.landing_page.landing_page.PostgresConnectionProvider")
    @patch("rest.landing_page.landing_page.get_company_info")
    def test_signed_in_homepage_shows_role_appropriate_app_link(
        self, mock_get_company_info, mock_connection_provider, app, role, app_url
    ):
        mock_get_company_info.return_value = CompanyInfo(
            product_name="Reinforcement Testing Platform",
            product_description="An adaptive testing platform.",
            contact_email="contact@bluesharklabs.com",
            contact_phone="+44 1234 567890",
            contact_address="Blue Shark Labs, Weston-super-Mare, UK",
        )

        with app.test_request_context("/"):
            g.user = SimpleNamespace(name="Test User", role=role)
            response = landing_page_route()

        assert f'href="{app_url}"' in response
        assert "Test User" in response
        assert "Guest" not in response
        assert "Log In" not in response
        assert "Sign Up" not in response
        assert (
            '<div class="hidden items-center gap-2 rounded-full border '
            'border-app-divider px-3 py-2 md:flex">'
        ) in response

    @pytest.mark.parametrize(
        ("role", "app_url"),
        [
            ("student", "/pr-block/"),
            ("lecturer", "/dashboard/lecturer"),
            ("admin", "/administrator/subjects"),
        ],
    )
    def test_privacy_page_returns_signed_in_users_to_their_app(
        self, app, role, app_url
    ):
        with app.test_request_context("/privacy"):
            g.user = SimpleNamespace(name="Test User", role=role)
            response = privacy_policy_route()

        assert f'href="{app_url}"' in response
        assert "Return to App" in response
        assert (
            '<div class="hidden items-center gap-2 rounded-full border '
            'border-app-divider px-3 py-2 md:flex">'
        ) in response
