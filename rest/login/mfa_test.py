# To Run: pytest rest/login/mfa_test.py

import time
from unittest.mock import patch

import pytest

from database.login.mfa import MfaSettings
from rest.login.login import LOCKOUT_MINUTES, MAX_FAILED_ATTEMPTS
from rest.login.mfa import INVALID_CODE_MESSAGE, MFA_PENDING_TTL_SECONDS, MFA_RESET_MESSAGE

USER_ID = "11111111-1111-1111-1111-111111111111"


def make_settings(**overrides):
    defaults = dict(
        email="lecturer@example.com",
        role="lecturer",
        mfa_enabled=True,
        mfa_secret="JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP",
        is_disabled=False,
        is_locked=False,
    )
    defaults.update(overrides)
    return MfaSettings(**defaults)


@pytest.fixture
def pending_client(client):
    with client.session_transaction() as sess:
        sess["mfa_pending_user_id"] = USER_ID
        sess["mfa_pending_since"] = int(time.time())
    return client


@patch("rest.login.mfa.PostgresConnectionProvider")
class TestMfaVerifyRoute:
    """Test the mfa_verify_route function"""

    def test_redirects_to_login_without_pending_sign_in(self, _provider, client):
        response = client.get("/login/mfa")

        assert response.status_code == 302
        assert response.location == "/login"

    def test_redirects_to_login_when_pending_sign_in_expired(self, _provider, client):
        with client.session_transaction() as sess:
            sess["mfa_pending_user_id"] = USER_ID
            sess["mfa_pending_since"] = int(time.time()) - MFA_PENDING_TTL_SECONDS - 1

        response = client.get("/login/mfa")

        assert response.location == "/login"
        with client.session_transaction() as sess:
            assert "mfa_pending_user_id" not in sess

    @patch("rest.login.mfa.get_mfa_settings")
    def test_renders_code_form(self, mock_get_settings, _provider, pending_client):
        mock_get_settings.return_value = make_settings()

        response = pending_client.get("/login/mfa")

        assert response.status_code == 200
        assert b'name="code"' in response.data

    @patch("rest.login.mfa.record_failed_login")
    @patch("rest.login.mfa.clear_failed_logins")
    @patch("rest.login.mfa.disable_mfa")
    @patch("rest.login.mfa.get_mfa_settings")
    def test_unreadable_secret_resets_mfa_and_signs_user_in(
        self, mock_get_settings, mock_disable, mock_clear, mock_record, provider, pending_client
    ):
        mock_get_settings.return_value = make_settings(mfa_secret=None)

        response = pending_client.get("/login/mfa")

        assert response.status_code == 302
        assert response.location == "/account/security"
        mock_disable.assert_called_once_with(provider.return_value, USER_ID)
        mock_clear.assert_called_once_with(provider.return_value, USER_ID)
        mock_record.assert_not_called()
        with pending_client.session_transaction() as sess:
            assert sess["user_id"] == USER_ID
            assert "mfa_pending_user_id" not in sess
            assert sess["_flashes"] == [("info", MFA_RESET_MESSAGE)]

    @patch("rest.login.mfa.clear_failed_logins")
    @patch("rest.login.mfa.claim_mfa_step", return_value=True)
    @patch("rest.login.mfa.matching_time_step", return_value=123)
    @patch("rest.login.mfa.get_mfa_settings")
    def test_valid_code_signs_user_in(
        self, mock_get_settings, _match, mock_claim, mock_clear, _provider, pending_client
    ):
        mock_get_settings.return_value = make_settings()

        response = pending_client.post("/login/mfa", data={"code": "123456"})

        assert response.status_code == 302
        assert "/dashboard/lecturer" in response.location
        mock_claim.assert_called_once()
        mock_clear.assert_called_once()
        with pending_client.session_transaction() as sess:
            assert sess["user_id"] == USER_ID
            assert sess["role"] == "lecturer"
            assert "mfa_pending_user_id" not in sess

    @patch("rest.login.mfa.record_failed_login")
    @patch("rest.login.mfa.matching_time_step", return_value=None)
    @patch("rest.login.mfa.get_mfa_settings")
    def test_invalid_code_records_failure(
        self, mock_get_settings, _match, mock_record, provider, pending_client
    ):
        mock_get_settings.return_value = make_settings()

        response = pending_client.post("/login/mfa", data={"code": "000000"})

        assert response.status_code == 400
        assert INVALID_CODE_MESSAGE in response.get_data(as_text=True)
        mock_record.assert_called_once_with(
            provider.return_value, USER_ID, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES
        )
        with pending_client.session_transaction() as sess:
            assert "user_id" not in sess

    @patch("rest.login.mfa.record_failed_login")
    @patch("rest.login.mfa.claim_mfa_step", return_value=False)
    @patch("rest.login.mfa.matching_time_step", return_value=123)
    @patch("rest.login.mfa.get_mfa_settings")
    def test_reused_code_is_rejected(
        self, mock_get_settings, _match, _claim, mock_record, _provider, pending_client
    ):
        mock_get_settings.return_value = make_settings()

        response = pending_client.post("/login/mfa", data={"code": "123456"})

        assert response.status_code == 400
        mock_record.assert_called_once()

    @patch("rest.login.mfa.matching_time_step")
    @patch("rest.login.mfa.get_mfa_settings")
    def test_locked_account_is_rejected_without_checking_code(
        self, mock_get_settings, mock_match, _provider, pending_client
    ):
        mock_get_settings.return_value = make_settings(is_locked=True)

        response = pending_client.post("/login/mfa", data={"code": "123456"})

        assert response.status_code == 429
        mock_match.assert_not_called()

    @patch("rest.login.mfa.get_mfa_settings")
    def test_disabled_account_is_sent_back_to_login(self, mock_get_settings, _provider, pending_client):
        mock_get_settings.return_value = make_settings(is_disabled=True)

        response = pending_client.post("/login/mfa", data={"code": "123456"})

        assert response.location == "/login"
