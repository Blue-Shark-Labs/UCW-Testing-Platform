from flask import abort, g, render_template, session

from database.helpers.database_helpers import get_assigned_tests, get_completed_tests
from rest.helpers.rest_helpers import login_required


@login_required(role="student")
def student_dashboard_route():
    student_id = _student_id()
    assigned_tests = get_assigned_tests(student_id) if student_id else []
    completed_tests = get_completed_tests(student_id) if student_id else []
    return render_template(
        "student_dashboard/page.html",
        assigned_tests=assigned_tests,
        completed_tests=completed_tests,
    )


def _student_id():
    user = getattr(g, "user", None)
    if str(getattr(user, "role", "student")).lower() != "student":
        abort(403)
    return getattr(user, "user_id", None) or session.get("user_id")