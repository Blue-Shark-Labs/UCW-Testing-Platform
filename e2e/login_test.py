# To Run: pytest e2e/login_test.py

import re
from unittest.mock import patch

import pytest
from playwright.sync_api import Page, expect

from database.login.mfa import MfaSettings
from database.login.user import User
from e2e.conftest import USER_ID
from rest.login.login import AccountLockedError

EMAIL = "student@example.com"


@pytest.fixture
def authenticate_user():
    with patch("rest.login.login.authenticate_user") as mock_authenticate_user:
        yield mock_authenticate_user


def fill_login_form(page: Page, email=EMAIL, password="password123"):
    page.goto("/login")
    page.get_by_label("Username").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Log In").click()


class TestLoginPage:
    def test_renders_login_form(self, page: Page):
        page.goto("/login")

        expect(page.get_by_role("heading", name="Log In")).to_be_visible()
        expect(page.get_by_label("Username")).to_be_focused()
        expect(page.get_by_label("Password")).to_have_attribute("type", "password")
        expect(page.get_by_role("link", name="Sign Up")).to_have_attribute("href", "/register")

    def test_empty_form_is_not_submitted(self, page: Page, authenticate_user):
        page.goto("/login")

        page.get_by_role("button", name="Log In").click()

        expect(page.get_by_label("Username")).to_have_js_property("validity.valueMissing", True)
        authenticate_user.assert_not_called()

    def test_wrong_credentials_show_error_and_keep_email(self, page: Page, authenticate_user):
        authenticate_user.return_value = None

        fill_login_form(page)

        expect(page.get_by_text("Incorrect email or password")).to_be_visible()
        expect(page.get_by_text("Accounts are locked for")).to_be_visible()
        expect(page.get_by_label("Username")).to_have_value(EMAIL)
        expect(page.get_by_label("Password")).to_have_value("")

    def test_locked_account_shows_lockout_message(self, page: Page, authenticate_user):
        authenticate_user.side_effect = AccountLockedError()

        fill_login_form(page)

        expect(page.get_by_text("Too many failed attempts")).to_be_visible()

    def test_mfa_user_is_asked_for_code(self, page: Page, authenticate_user):
        authenticate_user.return_value = User(
            user_id=USER_ID, email=EMAIL, password_hash="hash", role="student",
            is_disabled=False, mfa_enabled=True,
        )
        settings = MfaSettings(
            email=EMAIL, role="student", mfa_enabled=True, mfa_secret="JBSWY3DPEHPK3PXP",
            is_disabled=False, is_locked=False,
        )

        with patch("rest.login.mfa.get_mfa_settings", return_value=settings):
            fill_login_form(page)

            expect(page).to_have_url(re.compile("/login/mfa$"))
            expect(page.get_by_role("heading", name="Two-Factor Authentication")).to_be_visible()
            expect(page.get_by_label("Authentication code")).to_be_visible()
