# Query functions for a user's multi-factor authentication (TOTP) settings.

from dataclasses import dataclass


@dataclass(frozen=True)
class MfaSettings:
    email: str
    role: str
    mfa_enabled: bool
    # Set during enrolment before mfa_enabled is switched on.
    mfa_secret: str | None
    is_disabled: bool
    is_locked: bool


SELECT_MFA_SETTINGS = """
    SELECT email, role, mfa_enabled, mfa_secret, is_disabled,
           COALESCE(locked_until > NOW(), FALSE) AS is_locked
    FROM users
    WHERE user_id = %s;
"""

SAVE_PENDING_MFA_SECRET = """
    UPDATE users
    SET mfa_secret = %s, mfa_last_used_step = NULL
    WHERE user_id = %s AND mfa_enabled = FALSE;
"""

ENABLE_MFA = """
    UPDATE users
    SET mfa_enabled = TRUE
    WHERE user_id = %s AND mfa_secret IS NOT NULL;
"""

DISABLE_MFA = """
    UPDATE users
    SET mfa_enabled = FALSE, mfa_secret = NULL, mfa_last_used_step = NULL
    WHERE user_id = %s;
"""

# Conditional update so a code is accepted at most once, even under concurrent requests.
CLAIM_MFA_STEP = """
    UPDATE users
    SET mfa_last_used_step = %(step)s
    WHERE user_id = %(user_id)s
      AND (mfa_last_used_step IS NULL OR mfa_last_used_step < %(step)s)
    RETURNING user_id;
"""


def get_mfa_settings(connection_provider, user_id):
    """Fetches the user's MFA settings, or None if no such user exists."""
    with connection_provider.cursor() as cur:
        cur.execute(SELECT_MFA_SETTINGS, (user_id,))
        row = cur.fetchone()
    if row is None:
        return None
    return MfaSettings(*row)


def save_pending_mfa_secret(connection_provider, user_id, secret):
    """Stores a new secret for a user who has not yet enabled MFA."""
    with connection_provider.cursor() as cur:
        cur.execute(SAVE_PENDING_MFA_SECRET, (secret, user_id))


def enable_mfa(connection_provider, user_id):
    """Turns MFA on using the secret already saved for the user."""
    with connection_provider.cursor() as cur:
        cur.execute(ENABLE_MFA, (user_id,))


def disable_mfa(connection_provider, user_id):
    """Turns MFA off and discards the user's secret."""
    with connection_provider.cursor() as cur:
        cur.execute(DISABLE_MFA, (user_id,))


def claim_mfa_step(connection_provider, user_id, step):
    """Records the TOTP time step as used. Returns False if it (or a later step) was already used."""
    with connection_provider.cursor() as cur:
        cur.execute(CLAIM_MFA_STEP, {"user_id": user_id, "step": step})
        return cur.fetchone() is not None
