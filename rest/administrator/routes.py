from flask import Blueprint, abort, g, redirect, render_template, session, url_for

from rest.administrator.administrator import administrator_view_subjects_route
from rest.administrator.administrator import administrator_view_users_route
from rest.administrator.administrator import administrator_activate_deactivate_user_route
from rest.administrator.administrator import administrator_edit_user_route

administrator = Blueprint(
    "administrator",
    __name__,
    url_prefix="/administrator",
)

@administrator.before_request
def require_admin_role():
    if "user_id" not in session:
        return redirect(url_for("login_route"))
    user = getattr(g, "user", None)
    if user is None or user.role != "admin":
        abort(403)

administrator.add_url_rule("/subjects", view_func=administrator_view_subjects_route, methods=["GET", "POST"])
administrator.add_url_rule("/users", view_func=administrator_view_users_route, methods=["GET", "POST"])
administrator.add_url_rule("/users/activate-deactivate-user", view_func=administrator_activate_deactivate_user_route, methods=["POST"])
administrator.add_url_rule("/users/edit-user/<uuid:user_id>", view_func=administrator_edit_user_route, methods=["DELETE"])
administrator.add_url_rule("/edit-user/<uuid:user_id>", view_func=administrator_edit_user_route, methods=["DELETE"])