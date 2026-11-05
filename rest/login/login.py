from flask import redirect, render_template, request, session, url_for

from database.connection import PostgresConnectionProvider
from usecase.authenticate_user import authenticate_user

ROLE_DASHBOARD_ENDPOINTS = {
    "student": "student_dashboard_route",
    "lecturer": "lecturer_dashboard_route",
    "admin": "admin_dashboard_route",
}


def login_route():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        connection_provider = PostgresConnectionProvider()
        user = authenticate_user(connection_provider, email, password)
        if user is None:
            return render_template(
                "login/login.html",
                error="Incorrect email or password, or this account has been disabled.",
                email=email,
            )
        # Clearing first prevents session fixation from any pre-login session data.
        session.clear()
        session["user_id"] = str(user.user_id)
        session["role"] = user.role
        return redirect(url_for(ROLE_DASHBOARD_ENDPOINTS[user.role]))
    return render_template("login/login.html")
