from flask import Blueprint

from rest.lecturer.student_management import (
    approve_student_route,
    create_student_route,
    delete_student_route,
    edit_student_route,
    lecturer_management_route,
    toggle_student_status_route,
)

lecturer = Blueprint(
    "lecturer",
    __name__,
    url_prefix="/lecturer",
)

lecturer.add_url_rule("/student-management", view_func=lecturer_management_route, methods=["GET"])
lecturer.add_url_rule("/approve-student/<uuid:student_id>", view_func=approve_student_route, methods=["POST"])
lecturer.add_url_rule("/toggle-student-status/<uuid:student_id>", view_func=toggle_student_status_route, methods=["POST"])
lecturer.add_url_rule("/student/<uuid:student_id>/edit", view_func=edit_student_route, methods=["POST"])
lecturer.add_url_rule("/student/create", view_func=create_student_route, methods=["POST"])
lecturer.add_url_rule("/student/<uuid:student_id>/delete", view_func=delete_student_route, methods=["POST"])