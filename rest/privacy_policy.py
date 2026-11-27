from flask import g, render_template

from rest.helpers.rest_helpers import get_app_home_url


def privacy_policy_route():
    signed_in_user = getattr(g, "user", None)
    return render_template(
        "privacy_policy.html",
        signed_in_user=signed_in_user,
        app_home_url=get_app_home_url(signed_in_user),
    )
