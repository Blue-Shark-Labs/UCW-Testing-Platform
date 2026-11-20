from uuid import UUID

import psycopg
from flask import flash, redirect, render_template, request, session, url_for

from database.lecturer.quizzes import (
    create_question,
    create_quiz,
    delete_question,
    delete_quiz,
    list_questions,
    list_quizzes,
    list_subjects_with_pool_counts,
    toggle_quiz_status,
    update_question,
    update_quiz,
)


def _parse_uuid(raw_value: str) -> UUID | None:
    try:
        return UUID(str(raw_value).strip())
    except (ValueError, TypeError):
        return None


def _extract_question_options(form) -> tuple[list[tuple[str, bool]] | None, str | None]:
    """Validates 2 to 4 options with exactly 1 marked correct (FR-67)."""
    correct_slot = form.get("correct_option", "").strip()
    options: list[tuple[str, bool]] = []
    has_correct = False

    for idx in range(1, 5):
        text = form.get(f"option_{idx}", "").strip()
        if not text:
            if correct_slot == str(idx):
                return None, "The selected correct answer cannot be empty."
            continue

        if len(text) > 255:
            return None, "Answer choices must not exceed 255 characters."

        is_correct = correct_slot == str(idx)
        if is_correct:
            has_correct = True
        options.append((text, is_correct))

    if len(options) < 2 or len(options) > 4:
        return None, "Provide between 2 and 4 answer choices."

    if not has_correct:
        return None, "Select exactly one correct answer choice."

    return options, None


def quiz_management_route():
    quizzes = list_quizzes()
    subjects = list_subjects_with_pool_counts()
    questions = list_questions()

    search_query = request.args.get("q", "").strip().lower()
    subject_filter = request.args.get("subject", "").strip()
    active_tab = request.args.get("tab", "quizzes").strip()
    if active_tab not in {"quizzes", "questions"}:
        active_tab = "quizzes"

    filtered_quizzes = quizzes
    if subject_filter:
        filtered_quizzes = [
            q for q in filtered_quizzes if q["subject_id"] == subject_filter
        ]
    if search_query:
        filtered_quizzes = [
            q for q in filtered_quizzes
            if search_query in q["title"].lower()
            or search_query in q["description"].lower()
            or search_query in q["subject_name"].lower()
        ]

    filtered_questions = questions
    if subject_filter:
        filtered_questions = [
            item for item in filtered_questions if item["subject_id"] == subject_filter
        ]
    if search_query:
        filtered_questions = [
            item for item in filtered_questions
            if search_query in item["question_text"].lower()
            or search_query in item["subject_name"].lower()
            or any(search_query in opt["option_text"].lower() for opt in item["options"])
        ]

    stats = {
        "total_quizzes": len(quizzes),
        "active_quizzes": sum(1 for q in quizzes if q["is_active"]),
        "total_attempts": sum(q["attempt_count"] for q in quizzes),
        "total_questions": len(questions),
    }

    return render_template(
        "lecturer/quiz_management.html",
        quizzes=filtered_quizzes,
        questions=filtered_questions,
        subjects=subjects,
        stats=stats,
        search=request.args.get("q", ""),
        selected_subject=subject_filter,
        active_tab=active_tab,
    )


def create_quiz_route():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    subject_id = _parse_uuid(request.form.get("subject_id", ""))
    question_count_raw = request.form.get("question_count", "").strip()
    time_limit_raw = request.form.get("time_limit_minutes", "").strip()

    if not title or not subject_id:
        flash("Quiz title and target subject are required.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    if len(title) > 150:
        flash("Quiz title must not exceed 150 characters.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    if not question_count_raw.isdigit() or int(question_count_raw) < 1:
        flash("Question count must be a positive whole number.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    question_count = int(question_count_raw)

    if time_limit_raw == "":
        time_limit_minutes = None
    elif time_limit_raw.isdigit() and int(time_limit_raw) >= 1:
        time_limit_minutes = int(time_limit_raw)
    else:
        flash("Time limit must be a whole number of minutes or left blank.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    created_by = _parse_uuid(session.get("user_id", ""))

    try:
        create_quiz(
            subject_id=subject_id,
            created_by=created_by,
            title=title,
            description=description,
            question_count=question_count,
            time_limit_minutes=time_limit_minutes,
        )
        flash(f"Quiz '{title}' created successfully.", "success")
    except ValueError as err:
        flash(str(err), "error")
    except psycopg.Error:
        flash("A database error occurred while creating the quiz.", "error")

    return redirect(url_for("lecturer.quiz_management_route"))


def edit_quiz_route(test_id):
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    subject_id = _parse_uuid(request.form.get("subject_id", ""))
    question_count_raw = request.form.get("question_count", "").strip()
    time_limit_raw = request.form.get("time_limit_minutes", "").strip()

    if not title or not subject_id:
        flash("Quiz title and target subject are required.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    if len(title) > 150:
        flash("Quiz title must not exceed 150 characters.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    if not question_count_raw.isdigit() or int(question_count_raw) < 1:
        flash("Question count must be a positive whole number.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    question_count = int(question_count_raw)

    if time_limit_raw == "":
        time_limit_minutes = None
    elif time_limit_raw.isdigit() and int(time_limit_raw) >= 1:
        time_limit_minutes = int(time_limit_raw)
    else:
        flash("Time limit must be a whole number of minutes or left blank.", "error")
        return redirect(url_for("lecturer.quiz_management_route"))

    try:
        updated, error_msg = update_quiz(
            test_id=test_id,
            subject_id=subject_id,
            title=title,
            description=description,
            question_count=question_count,
            time_limit_minutes=time_limit_minutes,
        )
        if not updated:
            flash(error_msg or "Quiz not found.", "error")
        else:
            flash(f"Quiz '{title}' updated successfully.", "success")
    except psycopg.Error:
        flash("A database error occurred while updating the quiz.", "error")

    return redirect(url_for("lecturer.quiz_management_route"))


def toggle_quiz_status_route(test_id):
    try:
        new_active_state = toggle_quiz_status(test_id)
        if new_active_state is None:
            flash("Quiz not found.", "error")
        else:
            label = "activated" if new_active_state else "hidden from student dashboards"
            flash(f"Quiz {label} successfully.", "success")
    except psycopg.Error:
        flash("A database error occurred while updating quiz visibility.", "error")

    return redirect(url_for("lecturer.quiz_management_route"))


def delete_quiz_route(test_id):
    confirmed_archive = request.form.get("confirmed", "false") == "true"

    try:
        outcome, title = delete_quiz(test_id, confirmed_archive)
        if outcome == "not_found":
            flash("Quiz not found.", "error")
        elif outcome == "requires_confirmation":
            flash(
                f"'{title}' has student attempts. Please confirm archiving to "
                "preserve historical records.",
                "warning",
            )
        elif outcome == "archived":
            flash(
                f"Quiz '{title}' archived. Historical student attempts have been preserved.",
                "warning",
            )
        else:
            flash(f"Quiz '{title}' permanently deleted.", "success")
    except psycopg.Error:
        flash("A database error occurred while deleting the quiz.", "error")

    return redirect(url_for("lecturer.quiz_management_route"))


def create_question_route():
    subject_id = _parse_uuid(request.form.get("subject_id", ""))
    question_text = request.form.get("question_text", "").strip()

    if not subject_id or not question_text:
        flash("Subject and question prompt are required.", "error")
        return redirect(url_for("lecturer.quiz_management_route", tab="questions"))

    options, error_msg = _extract_question_options(request.form)
    if error_msg:
        flash(error_msg, "error")
        return redirect(url_for("lecturer.quiz_management_route", tab="questions"))

    try:
        create_question(subject_id, question_text, options)
        flash("Question added to subject pool.", "success")
    except psycopg.Error:
        flash("A database error occurred while adding the question.", "error")

    return redirect(url_for("lecturer.quiz_management_route", tab="questions"))


def edit_question_route(question_id):
    subject_id = _parse_uuid(request.form.get("subject_id", ""))
    question_text = request.form.get("question_text", "").strip()

    if not subject_id or not question_text:
        flash("Subject and question prompt are required.", "error")
        return redirect(url_for("lecturer.quiz_management_route", tab="questions"))

    options, error_msg = _extract_question_options(request.form)
    if error_msg:
        flash(error_msg, "error")
        return redirect(url_for("lecturer.quiz_management_route", tab="questions"))

    try:
        if update_question(question_id, subject_id, question_text, options):
            flash("Question updated successfully.", "success")
        else:
            flash("Question not found.", "error")
    except psycopg.Error:
        flash("A database error occurred while updating the question.", "error")

    return redirect(url_for("lecturer.quiz_management_route", tab="questions"))


def delete_question_route(question_id):
    try:
        if delete_question(question_id):
            flash("Question removed from active pool.", "success")
        else:
            flash("Question not found.", "error")
    except psycopg.Error:
        flash("A database error occurred while removing the question.", "error")

    return redirect(url_for("lecturer.quiz_management_route", tab="questions"))