# To Run: pytest usecase/get_landing_page_content_test.py

from unittest.mock import patch

from domain.entities.company_info import CompanyInfo
from usecase.get_landing_page_content import get_landing_page_content


class TestGetLandingPageContent:
    """Test the get_landing_page_content function"""

    @patch("usecase.get_landing_page_content.get_company_info")
    def test_get_landing_page_content_delegates_to_database_layer(self, mock_get_company_info):
        # ARRANGE
        expected = CompanyInfo(
            product_name="Reinforcement Testing Platform",
            product_description="A testing platform.",
            contact_email="contact@example.com",
            contact_phone="+44 1234 567890",
            contact_address="123 Example Street",
        )
        mock_get_company_info.return_value = expected
        connection_provider = object()

        # ACT
        result = get_landing_page_content(connection_provider)

        # ASSERT
        assert result is expected
        mock_get_company_info.assert_called_once_with(connection_provider)
