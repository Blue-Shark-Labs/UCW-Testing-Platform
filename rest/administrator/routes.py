from flask import Blueprint, render_template

from rest.administrator.administrator import administrator_view_subjects_route
from rest.administrator.administrator import administrator_edit_subject_route

administrator = Blueprint(
    "administrator",
    __name__,
    url_prefix="/administrator",
)

administrator.add_url_rule("/subjects", view_func=administrator_view_subjects_route, methods=["GET"])
administrator.add_url_rule("/edit-subject/<string:subject_id>", view_func=administrator_edit_subject_route, methods=["GET", "POST"])