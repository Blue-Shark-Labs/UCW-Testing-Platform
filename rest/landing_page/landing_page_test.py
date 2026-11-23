# To Run: pytest rest/landing_page/landing_page_test.py

from unittest.mock import patch

from database.landing_page.company_info import CompanyInfo
from rest.landing_page.landing_page import landing_page_route


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
        mock_get_company_info.assert_called_once_with(mock_connection_provider.return_value)
