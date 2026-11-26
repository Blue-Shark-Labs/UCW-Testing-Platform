import psycopg
from flask import abort, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from database.lecturer.students import (
    approve_student,
    create_student,
    delete_student,
    get_class_progress_summary,
    get_student_progress_detail,
    list_students,
    reject_student,
    toggle_student_status,
    update_student,
)
from rest.helpers.notifications import send_student_approval_email


def lecturer_management_route():
    rows = list_students()
    formatted_students = []

    for row in rows:
        (
            user_id,
            first_name,
            last_name,
            email,
            last_login_at,
            is_disabled,
            student_number,
            course_title,
            is_approved,
        ) = row

        if student_number is None:
            status = "Incomplete Profile"
        elif not is_approved:
            status = "Pending Approval"
        elif is_disabled:
            status = "Disabled"
        else:
            status = "Active"

        last_login = (
            last_login_at.strftime("%d %b %Y, %H:%M")
            if last_login_at else "Never"
        )

        formatted_students.append({
            "student_id": str(user_id),
            "student_number": student_number or "Not assigned",
            "first_name": first_name or "",
            "last_name": last_name or "",
            "name": f"{first_name or ''} {last_name or ''}".strip(),
            "email": email or "",
            "course": course_title or "Not assigned",
            "last_login": last_login,
            "status": status,
            "is_approved": bool(is_approved) if is_approved is not None else False,
            "is_disabled": bool(is_disabled),
        })

    search_query = request.args.get("q", "").strip().lower()
    if search_query:
        formatted_students = [
            student for student in formatted_students
            if search_query in student["name"].lower()
            or search_query in student["student_id"].lower()
            or search_query in student["student_number"].lower()
            or search_query in student["course"].lower()
            or search_query in student["email"].lower()
        ]

    class_summary = get_class_progress_summary()
    scored_students = [s["average_percentage"] for s in class_summary if s["average_percentage"] is not None]
    avg_score_display = (
        f"{round(sum(scored_students) / len(scored_students), 1)}%"
        if scored_students
        else "N/A"
    )

    stats = {
        "total_students": len(rows),
        "pending_approvals": sum(
            1 for row in rows
            if row[6] is not None and row[8] is False
        ),
        "active_tests": sum(s["completed_tests"] for s in class_summary),
        "avg_score": avg_score_display,
    }

    pagination = {
        "page": 1,
        "per_page": 10,
        "total": len(formatted_students),
        "first": 1 if formatted_students else 0,
        "last": len(formatted_students),
        "total_pages": 1,
        "has_prev": False,
        "has_next": False,
        "prev_num": 1,
        "next_num": 1,
    }

    return render_template(
        "lecturer/student_management.html",
        students=formatted_students,
        stats=stats,
        pagination=pagination,
        search=request.args.get("q", ""),
    )


def approve_student_route(student_id):
    approved_student = approve_student(student_id)
    if approved_student:
        email_sent = send_student_approval_email(
            approved_student["email"],
            approved_student["first_name"],
        )
        if email_sent:
            flash(
                f"Student approved and confirmation email sent to {approved_student['email']}.",
                "success",
            )
        else:
            flash(
                f"Student approved successfully (notification queued for {approved_student['email']}).",
                "success",
            )
    else:
        flash("Student profile not found.", "error")
    return redirect(url_for("lecturer.lecturer_management_route"))


def reject_student_route(student_id):
    try:
        outcome, rejected_user = reject_student(student_id)
        if outcome == "not_found":
            flash("Pending student registration not found.", "error")
        elif outcome == "already_approved":
            flash("Approved students cannot be rejected. Disable or terminate the account instead.", "error")
        else:
            flash(
                f"Registration for {rejected_user[0]} {rejected_user[1]} rejected and removed.",
                "warning",
            )
    except psycopg.Error:
        flash("A database error occurred while rejecting the student registration.", "error")
    return redirect(url_for("lecturer.lecturer_management_route"))


def toggle_student_status_route(student_id):
    new_disabled_state = toggle_student_status(student_id)
    if new_disabled_state is None:
        flash("Student account not found.", "error")
    else:
        status = "disabled" if new_disabled_state else "enabled"
        flash(f"Student account {status} successfully.", "success")
    return redirect(url_for("lecturer.lecturer_management_route"))


def edit_student_route(student_id):
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    course = request.form.get("course", "").strip()

    if not first_name or not last_name or not course:
        flash("First name, last name and course are required.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    try:
        updated = update_student(student_id, first_name, last_name, course)
        if not updated:
            flash("Student account not found.", "error")
        else:
            flash(f"Updated record for {first_name} {last_name}.", "success")
    except psycopg.Error:
        flash("A database error occurred while updating the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


def create_student_route():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    course = request.form.get("course", "").strip()
    password = request.form.get("password", "")

    if not all([first_name, last_name, email, course, password]):
        flash("All fields are required to create a student.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    if len(first_name) > 50 or len(last_name) > 50:
        flash("Names must not exceed 50 characters.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    if len(email) > 50 or len(course) > 100:
        flash("Email or course exceeds the permitted length.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    password_hash = generate_password_hash(password)

    try:
        student_number = create_student(
            first_name, last_name, email, password_hash, course
        )
        flash(
            f"Student {first_name} {last_name} created successfully "
            f"(Student Number: {student_number}).",
            "success",
        )
    except psycopg.errors.UniqueViolation:
        flash(f"A user with email '{email}' already exists.", "error")
    except psycopg.Error:
        flash("A database error occurred while creating the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


def delete_student_route(student_id):
    try:
        outcome, deleted_user = delete_student(student_id)
        if outcome == "anonymised":
            flash(
                f"Account for {deleted_user[0]} {deleted_user[1]} terminated and PII anonymised in compliance with GDPR (historical test attempts preserved).",
                "warning",
            )
        elif outcome == "not_found":
            flash("Student account not found.", "error")
        else:
            flash(
                f"Account for {deleted_user[0]} {deleted_user[1]} permanently deleted.",
                "success",
            )
    except psycopg.errors.ForeignKeyViolation:
        flash(
            "The student cannot be deleted because related records exist.",
            "error",
        )
    except psycopg.Error:
        flash("A database error occurred while terminating the student account.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


def student_progress_route():
    """FR-63: Aggregate class list showing cumulative points and overall average percentages."""
    class_list = get_class_progress_summary()
    search_query = request.args.get("q", "").strip().lower()
    if search_query:
        class_list = [
            s for s in class_list
            if search_query in s["name"].lower()
            or search_query in s["student_number"].lower()
            or search_query in s["course_title"].lower()
        ]

    scored = [s["average_percentage"] for s in class_list if s["average_percentage"] is not None]
    class_stats = {
        "total_students": len(class_list),
        "total_completed_tests": sum(s["completed_tests"] for s in class_list),
        "total_points": sum(s["cumulative_points"] for s in class_list),
        "class_average": f"{round(sum(scored) / len(scored), 1)}%" if scored else "N/A",
    }

    return render_template(
        "lecturer/student_progress.html",
        class_list=class_list,
        class_stats=class_stats,
        selected_student=None,
        search=request.args.get("q", ""),
    )


def student_progress_detail_route(student_id):
    """FR-64 & FR-65: Individual student test history and performance trajectory chart."""
    detail = get_student_progress_detail(student_id)
    if detail is None:
        abort(404)

    class_list = get_class_progress_summary()
    scored = [s["average_percentage"] for s in class_list if s["average_percentage"] is not None]
    class_stats = {
        "total_students": len(class_list),
        "total_completed_tests": sum(s["completed_tests"] for s in class_list),
        "total_points": sum(s["cumulative_points"] for s in class_list),
        "class_average": f"{round(sum(scored) / len(scored), 1)}%" if scored else "N/A",
    }

    return render_template(
        "lecturer/student_progress.html",
        class_list=class_list,
        class_stats=class_stats,
        selected_student=detail,
        search="",
    )