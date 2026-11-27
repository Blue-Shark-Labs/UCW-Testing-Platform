from flask import g, render_template, request, session

from database.lecturer.subjects import list_lecturer_subjects

def lecturer_view_subjects_route():
    search = (request.args.get("q") or "").strip()
    assigned_only = request.args.get("assigned") == "1"
    user = getattr(g, "user", None)
    lecturer_id = getattr(user, "user_id", None) or session.get("user_id")

    subjects = (
        list_lecturer_subjects(lecturer_id, search=search, assigned_only=assigned_only)
        if lecturer_id
        else []
    )

    return render_template(
        "lecturer/view_subjects.html",
        subjects=subjects,
        search=search,
        assigned_only=assigned_only,
    )