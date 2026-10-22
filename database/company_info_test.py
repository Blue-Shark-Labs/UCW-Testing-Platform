# To Run: pytest database/company_info_test.py

from contextlib import contextmanager
from unittest.mock import MagicMock

from database.company_info import get_company_info
from domain.entities.company_info import CompanyInfo


class FakeConnectionProvider:
    """Stands in for PostgresConnectionProvider, returning a fixed row from the cursor."""

    def __init__(self, row):
        self.cursor_mock = MagicMock()
        self.cursor_mock.fetchone.return_value = row

    @contextmanager
    def cursor(self):
        yield self.cursor_mock


class TestGetCompanyInfo:
    """Test the get_company_info function"""

    def test_get_company_info_maps_row_to_entity(self):
        # ARRANGE
        row = (
            "Reinforcement Testing Platform",
            "A testing platform.",
            "contact@example.com",
            "+44 1234 567890",
            "123 Example Street",
        )
        connection_provider = FakeConnectionProvider(row)

        # ACT
        result = get_company_info(connection_provider)

        # ASSERT
        assert result == CompanyInfo(
            product_name="Reinforcement Testing Platform",
            product_description="A testing platform.",
            contact_email="contact@example.com",
            contact_phone="+44 1234 567890",
            contact_address="123 Example Street",
        )
        connection_provider.cursor_mock.execute.assert_called_once()
