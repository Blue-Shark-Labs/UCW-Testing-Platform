"""REST layer: the delivery mechanism.

`create_app` wires each route handler to a URL. Handlers live one-per-file
and translate HTTP requests into database-layer calls. 
"""

from flask import Flask

from rest.home import home_route


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.add_url_rule("/", view_func=home_route, methods=["GET"])

    return app
