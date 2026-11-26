from flask import Blueprint

from rest.account.security import (
    mfa_disable_route,
    mfa_enable_route,
    mfa_setup_route,
    security_settings_route,
)

account = Blueprint("account", __name__, url_prefix="/account")
account.add_url_rule("/security", view_func=security_settings_route, methods=["GET"])
account.add_url_rule("/security/mfa/setup", view_func=mfa_setup_route, methods=["POST"])
account.add_url_rule("/security/mfa/enable", view_func=mfa_enable_route, methods=["POST"])
account.add_url_rule("/security/mfa/disable", view_func=mfa_disable_route, methods=["POST"])
