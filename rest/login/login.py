from flask import redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from rest.administrator.administrator import administrator_view_subjects_route

from database.connection import PostgresConnectionProvider
from database.login.user import clear_failed_logins, get_user_by_email, record_failed_login

# FR-11: lock the account after this many consecutive failed attempts.
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_MINUTES = 15

ROLE_DASHBOARD_ENDPOINTS = {
    "student": "student_dashboard.student_dashboard_route",
    "lecturer": "lecturer_dashboard_route",
    "admin": "administrator.administrator_view_subjects_route",
}

# Shown for every failure so real and unknown emails get identical responses.
LOCKOUT_POLICY_WARNING = (
    f"Accounts are locked for {LOCKOUT_MINUTES} minutes after {MAX_FAILED_ATTEMPTS} failed attempts."
)


class AccountLockedError(Exception):
    """Raised when a login is attempted on an account that is temporarily locked."""


def authenticate_user(connection_provider, email, password):
    """Returns the matching user if the credentials are valid and the account is active and approved, else None.

    Raises AccountLockedError if the account is locked from too many failed attempts.
    """
    user = get_user_by_email(connection_provider, email)
    if user is None or user.is_disabled or not user.is_approved:
        return None
    if user.is_locked:
        raise AccountLockedError()
    if not check_password_hash(user.password_hash, password):
        record_failed_login(connection_provider, user.user_id, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES)
        return None
    clear_failed_logins(connection_provider, user.user_id)
    return user


def login_route():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        connection_provider = PostgresConnectionProvider()
        try:
            user = authenticate_user(connection_provider, email, password)
        except AccountLockedError:
            return render_template(
                "login/login.html",
                error=f"Too many failed attempts. Please try again in {LOCKOUT_MINUTES} minutes.",
                email=email,
            ), 429
        if user is None:
            return render_template(
                "login/login.html",
                error="Incorrect email or password, or this account has been disabled.",
                warning=LOCKOUT_POLICY_WARNING,
                email=email,
            )
        # Clearing first prevents session fixation from any pre-login session data.
        session.clear()
        session["user_id"] = str(user.user_id)
        session["role"] = user.role
        return redirect(url_for(ROLE_DASHBOARD_ENDPOINTS[user.role]))
    return render_template("login/login.html")
