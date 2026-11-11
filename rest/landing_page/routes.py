from flask import Blueprint

from rest.landing_page.landing_page import landing_page_route

landing_page = Blueprint("landing_page", __name__)

landing_page.add_url_rule("/", view_func=landing_page_route, methods=["GET"])