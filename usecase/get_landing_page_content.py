# Use case: assemble the content shown to guests on the landing page.

from database.company_info import get_company_info


def get_landing_page_content(connection_provider):
    """Fetches the product and contact information shown on the landing page."""
    return get_company_info(connection_provider)
