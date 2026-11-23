# Query functions for the users table (login authentication).

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: str
    email: str
    password_hash: str
    role: str
    is_disabled: bool
    # Only students can be unapproved; other roles are always True.
    is_approved: bool = True
    is_locked: bool = False


SELECT_USER_BY_EMAIL = """
    SELECT u.user_id, u.email, u.password_hash, u.role, u.is_disabled,
           COALESCE(s.is_approved, TRUE) AS is_approved,
           COALESCE(u.locked_until > NOW(), FALSE) AS is_locked
    FROM users u
    LEFT JOIN students s ON s.user_id = u.user_id
    WHERE u.email = %s;
"""

# Single atomic UPDATE so concurrent failures can't race past the limit; the counter
# resets when the lock is applied so the user gets a fresh allowance once it expires.
RECORD_FAILED_LOGIN = """
    UPDATE users
    SET failed_login_attempts = CASE
            WHEN failed_login_attempts + 1 >= %(max_attempts)s THEN 0
            ELSE failed_login_attempts + 1
        END,
        locked_until = CASE
            WHEN failed_login_attempts + 1 >= %(max_attempts)s
                THEN NOW() + make_interval(mins => %(lockout_minutes)s)
            ELSE locked_until
        END
    WHERE user_id = %(user_id)s;
"""

CLEAR_FAILED_LOGINS = """
    UPDATE users
    SET failed_login_attempts = 0, locked_until = NULL
    WHERE user_id = %s;
"""


def get_user_by_email(connection_provider, email):
    """Fetches the user with the given email, or None if no such user exists."""
    with connection_provider.cursor() as cur:
        cur.execute(SELECT_USER_BY_EMAIL, (email,))
        row = cur.fetchone()
    if row is None:
        return None
    return User(*row)


def record_failed_login(connection_provider, user_id, max_attempts, lockout_minutes):
    """Increments the user's failed login counter, locking the account once max_attempts is reached."""
    with connection_provider.cursor() as cur:
        cur.execute(
            RECORD_FAILED_LOGIN,
            {"user_id": user_id, "max_attempts": max_attempts, "lockout_minutes": lockout_minutes},
        )


def clear_failed_logins(connection_provider, user_id):
    """Resets the user's failed login counter and any lock."""
    with connection_provider.cursor() as cur:
        cur.execute(CLEAR_FAILED_LOGINS, (user_id,))
