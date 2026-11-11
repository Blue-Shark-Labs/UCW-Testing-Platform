# Database helper functions for interacting with the PostgreSQL database.

from domain.entities.company_info import CompanyInfo
from domain.entities.user import User


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


def row_to_user(row):
    """Maps a users table row to a User domain entity."""
    user_id, email, password_hash, role, is_disabled, is_approved = row
    return User(
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        role=role,
        is_disabled=is_disabled,
        is_approved=is_approved,
    )
