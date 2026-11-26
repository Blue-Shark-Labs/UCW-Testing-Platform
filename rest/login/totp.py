# Time-based one-time password (TOTP) helpers for authenticator apps.

import base64
import hmac
import re
import time

import pyotp
import qrcode
import qrcode.image.svg

ISSUER_NAME = "Reinforcement Testing Platform"
CODE_PATTERN = re.compile(r"^\d{6}$")
# Accept the previous and next 30-second window to tolerate clock drift.
ALLOWED_DRIFT_STEPS = 1


def generate_mfa_secret():
    return pyotp.random_base32()


def provisioning_qr_data_uri(secret, email):
    """Returns an SVG QR code (as a data URI) that authenticator apps can scan."""
    uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER_NAME)
    svg = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage).to_string()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode("ascii")


def matching_time_step(secret, code, now=None):
    """Returns the time step the code is valid for, or None if it doesn't match."""
    code = (code or "").replace(" ", "")
    if not secret or not CODE_PATTERN.match(code):
        return None
    totp = pyotp.TOTP(secret)
    current_step = int(now if now is not None else time.time()) // totp.interval
    for step in range(current_step - ALLOWED_DRIFT_STEPS, current_step + ALLOWED_DRIFT_STEPS + 1):
        if hmac.compare_digest(totp.generate_otp(step), code):
            return step
    return None
