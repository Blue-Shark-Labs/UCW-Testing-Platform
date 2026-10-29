"""REST layer: the delivery mechanism.

`create_app` wires each route handler to a URL. Handlers live one-per-file
and translate HTTP requests into database-layer calls. 
"""

from flask import Flask, g, redirect, request, url_for
from types import SimpleNamespace

from rest.login.login import login_route
from rest.pr_block.routes import pr_block
from rest.sidebar_navigation import get_sidebar_navigation


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

    # For authetnication set g.user for each request otherwise default will be student,
    # this can be done in a before_request handler or a middleware depending on the authentication mechanism used.
    # That's up to you to figure out :)

    # This is just for manual testing, you can remove it when you implement your authentication mechanism.
    @app.before_request
    def set_test_user():
        g.user = SimpleNamespace(role="student")  # Change this to "lecturer" or "administrator" or "student" to test different roles

    @app.context_processor
    def inject_sidebar_navigation():
        # g is Flasks global context for the current request, it can be used to store user information
        user = getattr(g, "user", None)
        role = getattr(user, "role", "student")
        items = get_sidebar_navigation(role)

        def prepare_item(item):
            endpoint = item.get("endpoint")
            item["active"] = endpoint == request.endpoint
            item["href"] = url_for(endpoint) if endpoint in app.view_functions else "#"
            item["children"] = [prepare_item(child) for child in item.get("children", [])]
            item["active"] = item["active"] or any(child["active"] for child in item["children"])
            return item

        return {"sidebar_items": [prepare_item(item) for item in items]}

    return app
