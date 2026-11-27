# To Run: pytest e2e/account_security_test.py

import re
from unittest.mock import patch

import pyotp
import pytest
from playwright.sync_api import Page, expect

from database.login.mfa import MfaSettings

SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"


@pytest.fixture
def mfa_state():
    """Mocks the MFA queries with an in-memory user record that the routes can update."""
    state = {"mfa_enabled": False, "mfa_secret": None}

    def get_settings(_provider, _user_id):
        return MfaSettings(
            email="student@example.com", role="student", mfa_enabled=state["mfa_enabled"],
            mfa_secret=state["mfa_secret"], is_disabled=False, is_locked=False,
        )

    with patch("rest.account.security.get_mfa_settings", side_effect=get_settings), \
            patch("rest.account.security.generate_mfa_secret", return_value=SECRET), \
            patch("rest.account.security.save_pending_mfa_secret", side_effect=lambda _p, _u, secret: state.update(mfa_secret=secret)), \
            patch("rest.account.security.enable_mfa", side_effect=lambda _p, _u: state.update(mfa_enabled=True)), \
            patch("rest.account.security.disable_mfa", side_effect=lambda _p, _u: state.update(mfa_enabled=False, mfa_secret=None)), \
            patch("rest.account.security.claim_mfa_step", return_value=True) as claim_mfa_step:
        state["claim_mfa_step"] = claim_mfa_step
        yield state


def status_badge(page: Page):
    return page.locator("span", has_text=re.compile(r"^(On|Off)$"))


class TestAccountSecurityPage:
    def test_redirects_to_login_when_signed_out(self, page: Page):
        page.goto("/account/security")

        expect(page).to_have_url(re.compile("/login$"))

    def test_shows_mfa_off(self, page: Page, sign_in, mfa_state):
        sign_in()

        page.goto("/account/security")

        expect(page.get_by_role("heading", name="Two-factor authentication")).to_be_visible()
        expect(status_badge(page)).to_have_text("Off")
        expect(page.get_by_role("button", name="Set up two-factor authentication")).to_be_visible()

    def test_set_up_and_turn_on_mfa(self, page: Page, sign_in, mfa_state):
        sign_in()
        page.goto("/account/security")

        page.get_by_role("button", name="Set up two-factor authentication").click()
        expect(page.get_by_alt_text("QR code for your authenticator app")).to_be_visible()
        expect(page.get_by_text(SECRET)).to_be_visible()

        page.get_by_label("Enter the 6-digit code").fill(pyotp.TOTP(SECRET).now())
        page.get_by_role("button", name="Turn on").click()

        expect(page.get_by_role("status")).to_have_text("Two-factor authentication is now on.")
        expect(status_badge(page)).to_have_text("On")

    def test_wrong_code_shows_error(self, page: Page, sign_in, mfa_state):
        mfa_state["claim_mfa_step"].return_value = False
        sign_in()
        page.goto("/account/security")
        page.get_by_role("button", name="Set up two-factor authentication").click()

        page.get_by_label("Enter the 6-digit code").fill("000000")
        page.get_by_role("button", name="Turn on").click()

        expect(page.get_by_text("That code is incorrect or has already been used.")).to_be_visible()
        expect(page.get_by_alt_text("QR code for your authenticator app")).to_be_visible()
        expect(status_badge(page)).to_have_text("Off")

    def test_turn_off_mfa(self, page: Page, sign_in, mfa_state):
        mfa_state.update(mfa_enabled=True, mfa_secret=SECRET)
        sign_in()
        page.goto("/account/security")
        expect(status_badge(page)).to_have_text("On")

        page.get_by_label("Enter a current code").fill(pyotp.TOTP(SECRET).now())
        page.get_by_role("button", name="Turn off").click()

        expect(page.get_by_role("status")).to_have_text("Two-factor authentication has been turned off.")
        expect(status_badge(page)).to_have_text("Off")
