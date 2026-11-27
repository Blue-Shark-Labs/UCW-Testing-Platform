# To Run: pytest e2e/landing_page_test.py

import re
from unittest.mock import patch

import pytest
from playwright.sync_api import Page, expect

from database.landing_page.company_info import CompanyInfo

COMPANY_INFO = CompanyInfo(
    product_name="Reinforcement Testing Platform",
    product_description="Online multiple-choice tests for UCW students.",
    contact_email="hello@bluesharklabs.example",
    contact_phone="01234 567890",
    contact_address="1 Test Street, Testville",
)


@pytest.fixture(autouse=True)
def company_info():
    with patch("rest.landing_page.landing_page.get_company_info", return_value=COMPANY_INFO):
        yield


class TestLandingPage:
    def test_shows_company_info(self, page: Page):
        page.goto("/")

        expect(page).to_have_title(re.compile("Landing Page"))
        product_info = page.locator("#product-info")
        expect(product_info).to_contain_text(COMPANY_INFO.product_name)
        expect(product_info).to_contain_text(COMPANY_INFO.product_description)
        contact_info = page.locator("#contact-info")
        expect(contact_info).to_contain_text(COMPANY_INFO.contact_email)
        expect(contact_info).to_contain_text(COMPANY_INFO.contact_phone)
        expect(contact_info).to_contain_text(COMPANY_INFO.contact_address)

    def test_shows_gallery_images(self, page: Page):
        page.goto("/")

        expect(page.locator("#gallery img")).to_have_count(3)

    def test_carousel_buttons_change_slide(self, page: Page):
        page.goto("/")
        track = page.locator("#carousel-track")

        page.locator("#carousel-next").click()
        expect(track).to_have_attribute("style", re.compile(r"translateX\(-100%\)"))

        page.locator("#carousel-prev").click()
        expect(track).to_have_attribute("style", re.compile(r"translateX\(-?0%\)"))

    def test_carousel_dot_jumps_to_slide(self, page: Page):
        page.goto("/")

        page.get_by_role("button", name="Go to slide 3").click()

        expect(page.locator("#carousel-track")).to_have_attribute("style", re.compile(r"translateX\(-200%\)"))

    def test_menu_button_opens_and_closes_drawer(self, page: Page):
        page.goto("/")
        open_button = page.get_by_role("button", name="Open menu")

        open_button.click()
        expect(open_button).to_have_attribute("aria-expanded", "true")

        page.get_by_role("button", name="Close menu").click()
        expect(open_button).to_have_attribute("aria-expanded", "false")

    def test_log_in_link_opens_login_page(self, page: Page):
        page.goto("/")

        page.locator("header").get_by_role("link", name="Log In").click()

        expect(page).to_have_url(re.compile("/login$"))
        expect(page.get_by_role("heading", name="Log In")).to_be_visible()
