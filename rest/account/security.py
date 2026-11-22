from flask import flash, redirect, render_template, request, session, url_for

from database.connection import PostgresConnectionProvider
from database.login.mfa import (
    claim_mfa_step,
    disable_mfa,
    enable_mfa,
    get_mfa_settings,
    save_pending_mfa_secret,
)
from rest.helpers.rest_helpers import login_required
from rest.login.mfa import INVALID_CODE_MESSAGE
from rest.login.totp import generate_mfa_secret, matching_time_step, provisioning_qr_data_uri

SECURITY_TEMPLATE = "account/security.html"


def _redirect_to_settings():
    return redirect(url_for("account.security_settings_route"))


def _render_setup(secret, email, error=None, status_code=200):
    return render_template(
        SECURITY_TEMPLATE,
        mfa_enabled=False,
        setup_secret=secret,
        qr_code=provisioning_qr_data_uri(secret, email),
        error=error,
    ), status_code


def _verified_step(connection_provider, user_id, secret):
    step = matching_time_step(secret, request.form.get("code", ""))
    return step is not None and claim_mfa_step(connection_provider, user_id, step)


@login_required()
def security_settings_route():
    settings = get_mfa_settings(PostgresConnectionProvider(), session["user_id"])
    return render_template(SECURITY_TEMPLATE, mfa_enabled=settings.mfa_enabled)


@login_required()
def mfa_setup_route():
    connection_provider = PostgresConnectionProvider()
    user_id = session["user_id"]
    settings = get_mfa_settings(connection_provider, user_id)
    if settings.mfa_enabled:
        return _redirect_to_settings()
    secret = generate_mfa_secret()
    save_pending_mfa_secret(connection_provider, user_id, secret)
    return _render_setup(secret, settings.email)


@login_required()
def mfa_enable_route():
    connection_provider = PostgresConnectionProvider()
    user_id = session["user_id"]
    settings = get_mfa_settings(connection_provider, user_id)
    if settings.mfa_enabled or not settings.mfa_secret:
        return _redirect_to_settings()
    if not _verified_step(connection_provider, user_id, settings.mfa_secret):
        return _render_setup(settings.mfa_secret, settings.email, error=INVALID_CODE_MESSAGE, status_code=400)
    enable_mfa(connection_provider, user_id)
    flash("Two-factor authentication is now on.", "success")
    return _redirect_to_settings()


@login_required()
def mfa_disable_route():
    connection_provider = PostgresConnectionProvider()
    user_id = session["user_id"]
    settings = get_mfa_settings(connection_provider, user_id)
    if not settings.mfa_enabled:
        return _redirect_to_settings()
    if not _verified_step(connection_provider, user_id, settings.mfa_secret):
        return render_template(SECURITY_TEMPLATE, mfa_enabled=True, error=INVALID_CODE_MESSAGE), 400
    disable_mfa(connection_provider, user_id)
    flash("Two-factor authentication has been turned off.", "success")
    return _redirect_to_settings()
