# Company info entity definition. Represents the product and contact
# information shown to guests on the landing page.

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyInfo:
    product_name: str
    product_description: str
    contact_email: str
    contact_phone: str
    contact_address: str
