# To Run: pytest rest/account/security_test.py

from unittest.mock import patch

import pytest

from database.login.mfa import MfaSettings

USER_ID = "11111111-1111-1111-1111-111111111111"
SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"


def make_settings(**overrides):
    defaults = dict(
        email="student@example.com",
        role="student",
        mfa_enabled=False,
        mfa_secret=None,
        is_disabled=False,
        is_locked=False,
    )
    defaults.update(overrides)
    return MfaSettings(**defaults)


@pytest.fixture(autouse=True)
def provider():
    with patch("rest.account.security.PostgresConnectionProvider") as mock_provider, patch(
        "rest.router.PostgresConnectionProvider"
    ):
        yield mock_provider


@pytest.fixture
def signed_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = USER_ID
        sess["role"] = "student"
    return client


class TestSecuritySettingsRoute:
    """Test the security settings routes"""

    def test_requires_login(self, client):
        response = client.get("/account/security")

        assert response.status_code == 302
        assert response.location == "/login"

    @patch("rest.account.security.get_mfa_settings")
    def test_shows_setup_button_when_mfa_off(self, mock_get_settings, signed_in_client):
        mock_get_settings.return_value = make_settings()

        response = signed_in_client.get("/account/security")

        assert response.status_code == 200
        assert "Set up two-factor authentication" in response.get_data(as_text=True)

    @patch("rest.account.security.save_pending_mfa_secret")
    @patch("rest.account.security.get_mfa_settings")
    def test_setup_saves_secret_and_shows_qr_code(
        self, mock_get_settings, mock_save, provider, signed_in_client
    ):
        mock_get_settings.return_value = make_settings()

        response = signed_in_client.post("/account/security/mfa/setup")

        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "data:image/svg+xml;base64," in body
        _, user_id, secret = mock_save.call_args.args
        assert user_id == USER_ID
        assert secret in body

    @patch("rest.account.security.enable_mfa")
    @patch("rest.account.security.claim_mfa_step", return_value=True)
    @patch("rest.account.security.matching_time_step", return_value=123)
    @patch("rest.account.security.get_mfa_settings")
    def test_enable_turns_on_mfa_for_valid_code(
        self, mock_get_settings, _match, _claim, mock_enable, provider, signed_in_client
    ):
        mock_get_settings.return_value = make_settings(mfa_secret=SECRET)

        response = signed_in_client.post("/account/security/mfa/enable", data={"code": "123456"})

        assert response.status_code == 302
        mock_enable.assert_called_once_with(provider.return_value, USER_ID)

    @patch("rest.account.security.enable_mfa")
    @patch("rest.account.security.matching_time_step", return_value=None)
    @patch("rest.account.security.get_mfa_settings")
    def test_enable_rejects_invalid_code(self, mock_get_settings, _match, mock_enable, signed_in_client):
        mock_get_settings.return_value = make_settings(mfa_secret=SECRET)

        response = signed_in_client.post("/account/security/mfa/enable", data={"code": "000000"})

        assert response.status_code == 400
        mock_enable.assert_not_called()

    @patch("rest.account.security.disable_mfa")
    @patch("rest.account.security.claim_mfa_step", return_value=True)
    @patch("rest.account.security.matching_time_step", return_value=123)
    @patch("rest.account.security.get_mfa_settings")
    def test_disable_turns_off_mfa_for_valid_code(
        self, mock_get_settings, _match, _claim, mock_disable, provider, signed_in_client
    ):
        mock_get_settings.return_value = make_settings(mfa_enabled=True, mfa_secret=SECRET)

        response = signed_in_client.post("/account/security/mfa/disable", data={"code": "123456"})

        assert response.status_code == 302
        mock_disable.assert_called_once_with(provider.return_value, USER_ID)

    @patch("rest.account.security.disable_mfa")
    @patch("rest.account.security.matching_time_step", return_value=None)
    @patch("rest.account.security.get_mfa_settings")
    def test_disable_rejects_invalid_code(self, mock_get_settings, _match, mock_disable, signed_in_client):
        mock_get_settings.return_value = make_settings(mfa_enabled=True, mfa_secret=SECRET)

        response = signed_in_client.post("/account/security/mfa/disable", data={"code": "000000"})

        assert response.status_code == 400
        mock_disable.assert_not_called()
