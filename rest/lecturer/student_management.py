import psycopg
from flask import flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from database.lecturer.students import (
    approve_student,
    create_student,
    delete_student,
    list_students,
    toggle_student_status,
    update_student,
)


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

    stats = {
        "total_students": len(rows),
        "pending_approvals": sum(
            1 for row in rows
            if row[6] is not None and row[8] is False
        ),
        "active_tests": 12,
        "avg_score": "74.8%",
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
    if approve_student(student_id):
        flash("Student approved successfully.", "success")
    else:
        flash("Student profile not found.", "error")
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
        if outcome == "has_attempts":
            flash(
                "This student has existing test attempts and cannot "
                "be deleted. Disable the account instead.",
                "error",
            )
        elif outcome == "not_found":
            flash("Student account not found.", "error")
        else:
            flash(
                f"Account for {deleted_user[0]} {deleted_user[1]} deleted.",
                "success",
            )
    except psycopg.errors.ForeignKeyViolation:
        flash(
            "The student cannot be deleted because related records exist.",
            "error",
        )
    except psycopg.Error:
        flash("A database error occurred while deleting the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))