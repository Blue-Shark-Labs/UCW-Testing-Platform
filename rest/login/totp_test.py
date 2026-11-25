# To Run: pytest rest/login/totp_test.py

import pyotp

from rest.login.totp import matching_time_step, provisioning_qr_data_uri

SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
NOW = 1_700_000_000


def code_for_step(step):
    return pyotp.TOTP(SECRET).generate_otp(step)


class TestMatchingTimeStep:
    """Test the matching_time_step function"""

    def test_returns_current_step_for_current_code(self):
        step = NOW // 30
        assert matching_time_step(SECRET, code_for_step(step), now=NOW) == step

    def test_accepts_one_step_of_clock_drift(self):
        step = NOW // 30
        assert matching_time_step(SECRET, code_for_step(step - 1), now=NOW) == step - 1
        assert matching_time_step(SECRET, code_for_step(step + 1), now=NOW) == step + 1

    def test_rejects_codes_outside_drift_window(self):
        assert matching_time_step(SECRET, code_for_step(NOW // 30 - 2), now=NOW) is None

    def test_ignores_spaces_in_code(self):
        code = code_for_step(NOW // 30)
        assert matching_time_step(SECRET, f"{code[:3]} {code[3:]}", now=NOW) is not None

    def test_rejects_malformed_codes_and_missing_secret(self):
        assert matching_time_step(SECRET, "abcdef", now=NOW) is None
        assert matching_time_step(SECRET, "", now=NOW) is None
        assert matching_time_step(None, code_for_step(NOW // 30), now=NOW) is None


class TestProvisioningQrDataUri:
    """Test the provisioning_qr_data_uri function"""

    def test_returns_svg_data_uri(self):
        assert provisioning_qr_data_uri(SECRET, "student@example.com").startswith("data:image/svg+xml;base64,")
