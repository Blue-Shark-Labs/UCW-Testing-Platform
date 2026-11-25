from flask import g, render_template, request, session

from database.lecturer.subjects import list_lecturer_subjects


def lecturer_view_subjects_route():
    search = (request.args.get("q") or "").strip()
    user = getattr(g, "user", None)
    lecturer_id = getattr(user, "user_id", None) or session.get("user_id")

    subjects = list_lecturer_subjects(lecturer_id, search=search) if lecturer_id else []

    return render_template(
        "lecturer/view_subjects.html",
        subjects=subjects,
        search=search,
    )