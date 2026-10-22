# To Run: pytest rest/home_test.py

from unittest.mock import patch

from domain.entities.company_info import CompanyInfo
from rest.home import home_route


class TestHomeRoute:
    """Test the home_route function"""

    @patch("rest.home.get_landing_page_content")
    def test_home_route_renders(self, mock_get_landing_page_content, app):
        # ARRANGE
        mock_get_landing_page_content.return_value = CompanyInfo(
            product_name="Reinforcement Testing Platform",
            product_description="A testing platform.",
            contact_email="contact@example.com",
            contact_phone="+44 1234 567890",
            contact_address="123 Example Street",
        )

        # ACT
        with app.test_request_context("/"):
            response = home_route()

        # ASSERT
        assert "Reinforcement Testing Platform" in response
