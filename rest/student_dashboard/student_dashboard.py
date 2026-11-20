from flask import render_template, session

from database.helpers.database_helpers import (
    get_assigned_tests,
    get_completed_tests,
    submit_expired_test_attempts,
)


def student_dashboard_route():
    student_id = session["user_id"]
    if student_id:
        submit_expired_test_attempts(student_id)
    assigned_tests = get_assigned_tests(student_id) if student_id else []
    completed_tests = get_completed_tests(student_id) if student_id else []
    return render_template(
        "student_dashboard/page.html",
        assigned_tests=get_assigned_tests(student_id),
        completed_tests=get_completed_tests(student_id),
    )
