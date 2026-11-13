from flask import Blueprint, render_template

from rest.administrator.administrator import administrator_view_subjects_route
from rest.administrator.administrator import administrator_edit_subject_route
from rest.administrator.administrator import administrator_create_subject_route
from rest.administrator.administrator import administrator_view_users_route
from rest.administrator.administrator import administrator_activate_deactivate_user_route
from rest.administrator.administrator import administrator_edit_user_route
from rest.administrator.administrator import administrator_create_user_route

administrator = Blueprint(
    "administrator",
    __name__,
    url_prefix="/administrator",
)

administrator.add_url_rule("/subjects", view_func=administrator_view_subjects_route, methods=["GET"])
administrator.add_url_rule("/edit-subject/<string:subject_id>", view_func=administrator_edit_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/create-subject", view_func=administrator_create_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/users", view_func=administrator_view_users_route, methods=["GET"])
administrator.add_url_rule("/activate-deactivate-user/<int:user_id>/<string:action>", view_func=administrator_activate_deactivate_user_route, methods=["GET"])
administrator.add_url_rule("/edit-user/<int:user_id>", view_func=administrator_edit_user_route, methods=["GET", "POST", "DELETE"])
administrator.add_url_rule("/create-user", view_func=administrator_create_user_route, methods=["GET", "POST"])