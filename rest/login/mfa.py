from flask import flash, redirect, render_template, request, session, url_for
import time

from database.connection import PostgresConnectionProvider
from database.login.mfa import claim_mfa_step, disable_mfa, get_mfa_settings
from database.login.user import clear_failed_logins, record_failed_login
from rest.login.login import LOCKOUT_MINUTES, MAX_FAILED_ATTEMPTS, start_user_session
from rest.login.totp import matching_time_step

MFA_PENDING_TTL_SECONDS = 300
INVALID_CODE_MESSAGE = "That code is incorrect or has already been used."
EXPIRED_MESSAGE = "Your sign-in took too long. Please log in again."
MFA_RESET_MESSAGE = (
    "Two-factor authentication was turned off because its saved key could no longer be read. "
    "Please set it up again."
)


def _pending_user_id():
    user_id = session.get("mfa_pending_user_id")
    started = session.get("mfa_pending_since", 0)
    if user_id is None or time.time() - started > MFA_PENDING_TTL_SECONDS:
        return None
    return user_id


def mfa_verify_route():
    user_id = _pending_user_id()
    if user_id is None:
        session.clear()
        flash(EXPIRED_MESSAGE, "info")
        return redirect(url_for("login_route"))

    connection_provider = PostgresConnectionProvider()
    settings = get_mfa_settings(connection_provider, user_id)
    if settings is None or settings.is_disabled or not settings.mfa_enabled:
        session.clear()
        return redirect(url_for("login_route"))
    if settings.is_locked:
        return render_template(
            "login/mfa.html",
            error=f"Too many failed attempts. Please try again in {LOCKOUT_MINUTES} minutes.",
        ), 429
    if settings.needs_reenrolment:
        # No code can ever match, so rely on the already-verified password and prompt re-enrolment.
        disable_mfa(connection_provider, user_id)
        clear_failed_logins(connection_provider, user_id)
        response = start_user_session(user_id, settings.role, endpoint="account.security_settings_route")
        flash(MFA_RESET_MESSAGE, "info")
        return response
    if request.method == "GET":
        return render_template("login/mfa.html")

    step = matching_time_step(settings.mfa_secret, request.form.get("code", ""))
    if step is None or not claim_mfa_step(connection_provider, user_id, step):
        record_failed_login(connection_provider, user_id, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES)
        return render_template("login/mfa.html", error=INVALID_CODE_MESSAGE), 400

    clear_failed_logins(connection_provider, user_id)
    return start_user_session(user_id, settings.role)
