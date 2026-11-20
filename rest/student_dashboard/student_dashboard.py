from flask import render_template, session

from database.helpers.database_helpers import get_assigned_tests, get_completed_tests
from rest.helpers.rest_helpers import login_required


@login_required(role="student")
def student_tests_route():
    # Only ever read the student's own data, from the signed session.
    student_id = session["user_id"]
    return render_template(
        "student_dashboard/page.html",
        assigned_tests=get_assigned_tests(student_id),
        completed_tests=get_completed_tests(student_id),
    )
