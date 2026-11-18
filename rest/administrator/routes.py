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

@administrator.before_request
def require_admin_role():
    if "user_id" not in session:
        return redirect(url_for("login_route"))
    user = getattr(g, "user", None)
    role = getattr(user, "role", None) or session.get("role")
    if role != "admin":
        return redirect(url_for("root_route"))
        
administrator.add_url_rule("/subjects", view_func=administrator_view_subjects_route, methods=["GET"])
administrator.add_url_rule("/subjects/edit-subject/<uuid:subject_id>", view_func=administrator_edit_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/subjects/create-subject", view_func=administrator_create_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/edit-subject/<uuid:subject_id>", view_func=administrator_edit_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/create-subject", view_func=administrator_create_subject_route, methods=["GET", "POST"])
administrator.add_url_rule("/users", view_func=administrator_view_users_route, methods=["GET"])
administrator.add_url_rule("/users/activate-deactivate-user", view_func=administrator_activate_deactivate_user_route, methods=["POST"])
administrator.add_url_rule("/users/edit-user/<uuid:user_id>", view_func=administrator_edit_user_route, methods=["GET", "POST", "DELETE"])
administrator.add_url_rule("/users/create-user", view_func=administrator_create_user_route, methods=["GET", "POST"])
administrator.add_url_rule("/edit-user/<uuid:user_id>", view_func=administrator_edit_user_route, methods=["GET", "POST", "DELETE"])
administrator.add_url_rule("/create-user", view_func=administrator_create_user_route, methods=["GET", "POST"])