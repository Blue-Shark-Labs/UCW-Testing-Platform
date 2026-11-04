# Database helper functions for interacting with the PostgreSQL database.

from domain.entities.company_info import CompanyInfo


def row_to_company_info(row):
    """Maps a company_info table row to a CompanyInfo domain entity."""
    product_name, product_description, contact_email, contact_phone, contact_address = row
    return CompanyInfo(
        product_name=product_name,
        product_description=product_description,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_address=contact_address,
    )
