from flask import g, render_template, session

from database.lecturer.quizzes import list_questions, list_quizzes
from database.lecturer.students import get_class_progress_summary, list_students
from database.lecturer.subjects import list_lecturer_subjects


def lecturer_dashboard_route():
    user = getattr(g, "user", None)
    lecturer_id = getattr(user, "user_id", None) or session.get("user_id")

    students = list_students()
    quizzes = list_quizzes()
    questions = list_questions()
    subjects = list_lecturer_subjects(lecturer_id) if lecturer_id else []
    class_summary = get_class_progress_summary()

    scored = [s["average_percentage"] for s in class_summary if s["average_percentage"] is not None]
    class_average = f"{round(sum(scored) / len(scored), 1)}%" if scored else "N/A"

    pending_students = [
        {
            "student_id": str(row[0]),
            "name": f"{row[1] or ''} {row[2] or ''}".strip(),
            "email": row[3] or "",
            "student_number": row[6],
            "course": row[7] or "Not assigned",
        }
        for row in students
        if row[6] is not None and row[8] is False
    ]

    stats = {
        "total_students": len(students),
        "pending_approvals": len(pending_students),
        "active_quizzes": sum(1 for q in quizzes if q["is_active"]),
        "total_quizzes": len(quizzes),
        "total_questions": len(questions),
        "assigned_subjects": sum(1 for s in subjects if s.get("is_assigned")),
        "total_subjects": len(subjects),
        "total_attempts": sum(q["attempt_count"] for q in quizzes),
        "class_average": class_average,
    }

    return render_template(
        "lecturer/dashboard.html",
        lecturer_name=getattr(user, "name", "Lecturer"),
        stats=stats,
        pending_students=pending_students[:5],
        recent_quizzes=quizzes[:5],
    )