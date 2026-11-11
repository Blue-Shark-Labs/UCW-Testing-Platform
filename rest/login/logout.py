from flask import flash, redirect, session, url_for

SIGN_OUT_MESSAGE = "You have been signed out successfully."


def logout_route():
    session.clear()
    flash(SIGN_OUT_MESSAGE, "success")
    response = redirect(url_for("login_route"))
    response.headers["Cache-Control"] = "no-store"
    return response
