# Use case: verify a user's credentials before granting access to the platform.

from werkzeug.security import check_password_hash

from database.login.user import clear_failed_logins, get_user_by_email, record_failed_login

# FR-11: lock the account after this many consecutive failed attempts.
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_MINUTES = 15


class AccountLockedError(Exception):
    """Raised when a login is attempted on an account that is temporarily locked."""


def authenticate_user(connection_provider, email, password):
    """Returns the matching user if the credentials are valid and the account isn't disabled, else None.

    Raises AccountLockedError if the account is locked from too many failed attempts.
    """
    user = get_user_by_email(connection_provider, email)
    if user is None or user.is_disabled:
        return None
    if user.is_locked:
        raise AccountLockedError()
    if not check_password_hash(user.password_hash, password):
        record_failed_login(connection_provider, user.user_id, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES)
        return None
    clear_failed_logins(connection_provider, user.user_id)
    return user
