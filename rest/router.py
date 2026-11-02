"""REST layer: the delivery mechanism.

`create_app` wires each route handler to a URL. Handlers live one-per-file
and translate HTTP requests into database-layer calls. 
"""

from flask import Flask, redirect, url_for

from rest.login.login import login_route
from rest.pr_block.routes import pr_block


def root_route():
    return redirect(url_for("login_route"))


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.add_url_rule("/", view_func=root_route, methods=["GET"])
    app.add_url_rule("/login", view_func=login_route, methods=["GET"])
    app.register_blueprint(pr_block)

    return app
