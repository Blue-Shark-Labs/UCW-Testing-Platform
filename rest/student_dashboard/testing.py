from uuid import UUID

from flask import abort, g, jsonify, render_template, request, url_for

from database.helpers.database_helpers import (
    save_test_answer,
    start_or_resume_test_attempt,
    submit_test_attempt,
)


def take_test_route(test_id):
    student_id = _student_id()
    attempt = start_or_resume_test_attempt(test_id, student_id)
    if attempt is None:
        abort(404)

    if (
        attempt["time_limit_minutes"] is not None
        and attempt["seconds_remaining"] == 0
    ):
        result = submit_test_attempt(
            test_id,
            attempt["attempt_id"],
            student_id,
        )
        if result is None:
            abort(404)
        return _render_result(attempt["test_name"], result)

    return render_template(
        "student_dashboard/testing.html",
        attempt=attempt,
        submit_url=url_for(
            "student_dashboard.submit_test",
            test_id=test_id,
            attempt_id=attempt["attempt_id"],
        ),
        save_answer_url=url_for(
            "student_dashboard.save_test_answer",
            test_id=test_id,
            attempt_id=attempt["attempt_id"],
        ),
    )


def save_test_answer_route(test_id, attempt_id):
    student_id = _student_id()
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        abort(400)
    question_id = payload.get("question_id")
    option_id = payload.get("option_id")
    if not question_id or not option_id:
        abort(400)
    try:
        question_id = UUID(str(question_id))
        option_id = UUID(str(option_id))
    except ValueError:
        abort(400)

    saved = save_test_answer(
        test_id,
        attempt_id,
        student_id,
        question_id,
        option_id,
    )
    if not saved:
        abort(409)
    return jsonify({"saved": True})


def submit_test_route(test_id, attempt_id):
    student_id = _student_id()
    try:
        answers = {
            key[len("answer_"):]: UUID(value)
            for key, value in request.form.items()
            if key.startswith("answer_")
        }
    except ValueError:
        abort(400)
    try:
        result = submit_test_attempt(
            test_id,
            attempt_id,
            student_id,
            answers,
        )
    except ValueError:
        abort(400)
    if result is None:
        abort(404)

    return _render_result(result["test_name"], result)


def _render_result(test_name, result):
    return render_template(
        "student_dashboard/test_result.html",
        test_name=test_name,
        result=result,
    )


def _student_id():
    user = getattr(g, "user", None)
    if str(getattr(user, "role", "")).lower() != "student":
        abort(403)
    student_id = getattr(user, "user_id", None)
    if not student_id:
        abort(403)
    return student_id
