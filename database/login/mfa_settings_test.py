# To Run: pytest database/login/mfa_settings_test.py

from contextlib import contextmanager
from unittest.mock import MagicMock

from database.login.mfa import MfaSettings, get_mfa_settings, save_pending_mfa_secret

SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"


class FakeConnectionProvider:
    """Stands in for PostgresConnectionProvider, returning a fixed row from the cursor."""

    def __init__(self, row=None):
        self.cursor_mock = MagicMock()
        self.cursor_mock.fetchone.return_value = row

    @contextmanager
    def cursor(self):
        yield self.cursor_mock


def saved_secret_column():
    connection_provider = FakeConnectionProvider()
    save_pending_mfa_secret(connection_provider, "user-1", SECRET)
    _, (stored, user_id) = connection_provider.cursor_mock.execute.call_args.args
    assert user_id == "user-1"
    return stored


class TestMfaSecretEncryption:
    """Test that MFA secrets are encrypted at rest"""

    def test_saved_secret_is_not_plaintext(self):
        assert SECRET not in saved_secret_column()

    def test_saved_secret_round_trips_through_get(self):
        # ARRANGE
        row = ("student@example.com", "student", True, saved_secret_column(), False, False)

        # ACT
        result = get_mfa_settings(FakeConnectionProvider(row), "user-1")

        # ASSERT
        assert result == MfaSettings("student@example.com", "student", True, SECRET, False, False)

    def test_unreadable_secret_is_treated_as_missing(self, monkeypatch):
        # ARRANGE
        stored = saved_secret_column()
        monkeypatch.setenv("SECRET_KEY", "a-different-secret-key")
        row = ("student@example.com", "student", True, stored, False, False)

        # ACT
        result = get_mfa_settings(FakeConnectionProvider(row), "user-1")

        # ASSERT
        assert result.mfa_secret is None
