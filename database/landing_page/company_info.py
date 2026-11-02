# Query functions for the company_info table (landing page product + contact info).

from database.helpers.database_helpers import row_to_company_info

SELECT_COMPANY_INFO = """
    SELECT product_name, product_description, contact_email, contact_phone, contact_address
    FROM company_info
    WHERE company_info_id = 'main';
"""


def get_company_info(connection_provider):
    """Fetches the singleton company/product info row shown on the landing page."""
    with connection_provider.cursor() as cur:
        cur.execute(SELECT_COMPANY_INFO)
        row = cur.fetchone()
    return row_to_company_info(row)
