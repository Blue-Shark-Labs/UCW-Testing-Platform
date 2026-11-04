"""REST layer: the delivery mechanism.

`create_app` wires each route handler to a URL. Handlers live one-per-file
and translate HTTP requests into database-layer calls. 
"""

import os

from flask import Flask, redirect, url_for

from rest.dashboard.admin_dashboard import admin_dashboard_route
from rest.dashboard.lecturer_dashboard import lecturer_dashboard_route
from rest.dashboard.student_dashboard import student_dashboard_route
from rest.landing_page.routes import landing_page
from rest.login.login import login_route
from rest.login.register import register_route
from rest.pr_block.routes import pr_block


def root_route():
    return redirect(url_for("login_route"))


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # SECRET_KEY signs the session cookie; falls back to a dev-only value so local
    # setup works without extra config, but production must set a real secret.
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key")
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SECRET_KEY") is not None,
    )

    app.add_url_rule("/", view_func=root_route, methods=["GET"])
    app.add_url_rule("/login", view_func=login_route, methods=["GET", "POST"])
    app.add_url_rule("/register", view_func=register_route, methods=["GET"])
    app.add_url_rule("/dashboard/student", view_func=student_dashboard_route, methods=["GET"])
    app.add_url_rule("/dashboard/lecturer", view_func=lecturer_dashboard_route, methods=["GET"])
    app.add_url_rule("/dashboard/admin", view_func=admin_dashboard_route, methods=["GET"])
    app.register_blueprint(landing_page)
    app.register_blueprint(pr_block)

    return app
