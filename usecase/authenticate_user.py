# Use case: verify a user's credentials before granting access to the platform.

from werkzeug.security import check_password_hash

from database.login.user import get_user_by_email


def authenticate_user(connection_provider, email, password):
    """Returns the matching user if the credentials are valid and the account is active and approved, else None."""
    user = get_user_by_email(connection_provider, email)
    if user is None or user.is_disabled or not user.is_approved:
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    return user
