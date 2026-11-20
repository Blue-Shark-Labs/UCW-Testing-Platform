from flask import Blueprint, g, redirect, session, url_for

from rest.lecturer.quiz_management import (
    create_question_route,
    create_quiz_route,
    delete_question_route,
    delete_quiz_route,
    edit_question_route,
    edit_quiz_route,
    quiz_management_route,
    toggle_quiz_status_route,
)
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


@lecturer.before_request
def require_lecturer_role():
    if "user_id" not in session:
        return redirect(url_for("login_route"))

    user = getattr(g, "user", None)
    role = getattr(user, "role", None) or session.get("role")
    if role != "lecturer":
        return redirect(url_for("login_route"))


# Student management routes
lecturer.add_url_rule("/student-management", view_func=lecturer_management_route, methods=["GET"])
lecturer.add_url_rule("/approve-student/<uuid:student_id>", view_func=approve_student_route, methods=["POST"])
lecturer.add_url_rule("/toggle-student-status/<uuid:student_id>", view_func=toggle_student_status_route, methods=["POST"])
lecturer.add_url_rule("/student/<uuid:student_id>/edit", view_func=edit_student_route, methods=["POST"])
lecturer.add_url_rule("/student/create", view_func=create_student_route, methods=["POST"])
lecturer.add_url_rule("/student/<uuid:student_id>/delete", view_func=delete_student_route, methods=["POST"])

# Quiz & question pool management routes
lecturer.add_url_rule("/quiz-management", view_func=quiz_management_route, methods=["GET"])
lecturer.add_url_rule("/quiz/create", view_func=create_quiz_route, methods=["POST"])
lecturer.add_url_rule("/quiz/<uuid:test_id>/edit", view_func=edit_quiz_route, methods=["POST"])
lecturer.add_url_rule("/quiz/<uuid:test_id>/toggle-status", view_func=toggle_quiz_status_route, methods=["POST"])
lecturer.add_url_rule("/quiz/<uuid:test_id>/delete", view_func=delete_quiz_route, methods=["POST"])
lecturer.add_url_rule("/question/create", view_func=create_question_route, methods=["POST"])
lecturer.add_url_rule("/question/<uuid:question_id>/edit", view_func=edit_question_route, methods=["POST"])
lecturer.add_url_rule("/question/<uuid:question_id>/delete", view_func=delete_question_route, methods=["POST"])