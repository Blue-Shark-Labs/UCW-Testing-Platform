from flask import abort, g, render_template, session

from database.helpers.database_helpers import (
    get_assigned_tests,
    get_completed_tests,
    submit_expired_test_attempts,
)
from rest.helpers.rest_helpers import login_required


@login_required(role="student")
def student_dashboard_route():
    student_id = session["user_id"]
    submit_expired_test_attempts(student_id)
    assigned_tests = get_assigned_tests(student_id)
    completed_tests = get_completed_tests(student_id)
    return render_template(
        "student_dashboard/page.html",
        assigned_tests=assigned_tests,
        completed_tests=completed_tests,
    )
