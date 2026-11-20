from flask import Blueprint, render_template, request

from database.helpers.database_helpers import get_active_subjects, get_subject_leaderboard
from rest.helpers.rest_helpers import login_required

leaderboards = Blueprint("leaderboards", __name__)


@leaderboards.get("/leaderboards")
@login_required(role="student")
def subject_leaderboards_route():
    subjects = get_active_subjects()
    selected_subject_id = request.args.get("subject_id", type=str)
    subject_ids = {str(subject["subject_id"]) for subject in subjects}

    if selected_subject_id not in subject_ids:
        selected_subject_id = str(subjects[0]["subject_id"]) if subjects else None

    selected_subject = next(
        (subject for subject in subjects if str(subject["subject_id"]) == selected_subject_id),
        None,
    )
    leaderboard = get_subject_leaderboard(selected_subject_id) if selected_subject_id else []

    return render_template(
        "dashboard/leaderboards.html",
        subjects=subjects,
        selected_subject=selected_subject,
        leaderboard=leaderboard,
    )
