from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from database.connection import PostgresConnectionProvider
from werkzeug.security import generate_password_hash
import psycopg


lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")


@lecturer_bp.route("/student-management", methods=["GET"])
def lecturer_management_route():

    provider = PostgresConnectionProvider()

    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.last_login_at,
                u.is_disabled,
                s.student_number,
                s.course_title,
                s.is_approved
            FROM users u
            LEFT JOIN students s ON u.user_id = s.user_id
            WHERE u.role = 'student'
            ORDER BY u.last_name, u.first_name;
        """)

        rows = cur.fetchall()

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
            is_approved
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
            "is_disabled": bool(is_disabled)
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
        "avg_score": "74.8%"
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
        "next_num": 1
    }

    return render_template(
        "lecturer/student_management.html",
        students=formatted_students,
        stats=stats,
        pagination=pagination,
        search=request.args.get("q", "")
    )


@lecturer_bp.route("/approve-student/<student_id>", methods=["POST"])
def approve_student_route(student_id):

    provider = PostgresConnectionProvider()

    with provider.cursor() as cur:
        cur.execute("""
            UPDATE students
            SET is_approved = TRUE
            WHERE user_id = %s
            RETURNING user_id;
        """, (student_id,))

        result = cur.fetchone()

    if result:
        flash("Student approved successfully.", "success")
    else:
        flash("Student profile not found.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


@lecturer_bp.route("/toggle-student-status/<student_id>", methods=["POST"])
def toggle_student_status_route(student_id):

    provider = PostgresConnectionProvider()

    with provider.cursor() as cur:
        cur.execute("""
            UPDATE users
            SET is_disabled = NOT is_disabled
            WHERE user_id = %s
              AND role = 'student'
            RETURNING is_disabled;
        """, (student_id,))

        result = cur.fetchone()

    if result is None:
        flash("Student account not found.", "error")
    else:
        status = "disabled" if result[0] else "enabled"
        flash(f"Student account {status} successfully.", "success")

    return redirect(url_for("lecturer.lecturer_management_route"))


# STAGE 4: EDIT STUDENT

@lecturer_bp.route("/student/<student_id>/edit", methods=["POST"])
def edit_student_route(student_id):

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    course = request.form.get("course", "").strip()

    if not first_name or not last_name or not course:
        flash("First name, last name and course are required.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    provider = PostgresConnectionProvider()

    try:
        with provider.cursor() as cur:

            # Update the user's personal details.
            cur.execute("""
                UPDATE users
                SET first_name = %s,
                    last_name = %s
                WHERE user_id = %s
                  AND role = 'student'
                RETURNING user_id;
            """, (first_name, last_name, student_id))

            user = cur.fetchone()

            if user is None:
                flash("Student account not found.", "error")
                return redirect(url_for("lecturer.lecturer_management_route"))

            # Update the profile, or create it if it is incomplete.
            # A newly created profile remains pending approval.
            cur.execute("""
                INSERT INTO students (
                    user_id,
                    student_number,
                    course_title
                )
                VALUES (
                    %s,
                    'S' || LPAD(nextval('student_number_seq')::TEXT, 7, '0'),
                    %s
                )
                ON CONFLICT (user_id)
                DO UPDATE SET course_title = EXCLUDED.course_title;
            """, (student_id, course))

        flash(
            f"Updated record for {first_name} {last_name}.",
            "success"
        )

    except psycopg.Error:
        flash("A database error occurred while updating the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


# STAGE 5: CREATE STUDENT

@lecturer_bp.route("/student/create", methods=["POST"])
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

    provider = PostgresConnectionProvider()

    try:
        with provider.cursor() as cur:

            # Create the user account.
            cur.execute("""
                INSERT INTO users (
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    role,
                    is_disabled
                )
                VALUES (%s, %s, %s, %s, 'student', FALSE)
                RETURNING user_id;
            """, (
                first_name,
                last_name,
                email,
                password_hash
            ))

            user_id = cur.fetchone()[0]

            # Create the student profile using an automatically generated
            # student number. Both inserts commit together.
            cur.execute("""
                INSERT INTO students (
                    user_id,
                    student_number,
                    course_title,
                    is_approved
                )
                VALUES (
                    %s,
                    'S' || LPAD(nextval('student_number_seq')::TEXT, 7, '0'),
                    %s,
                    TRUE
                )
                RETURNING student_number;
            """, (user_id, course))

            student_number = cur.fetchone()[0]

        flash(
            f"Student {first_name} {last_name} created successfully "
            f"(Student Number: {student_number}).",
            "success"
        )

    except psycopg.errors.UniqueViolation:
        flash(f"A user with email '{email}' already exists.", "error")

    except psycopg.Error:
        flash("A database error occurred while creating the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


# STAGE 6: DELETE STUDENT

@lecturer_bp.route("/student/<student_id>/delete", methods=["POST"])
def delete_student_route(student_id):

    provider = PostgresConnectionProvider()

    try:
        with provider.cursor() as cur:

            # Check whether the student has existing test attempts.
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM test_attempts
                    WHERE user_id = %s
                );
            """, (student_id,))

            has_attempts = cur.fetchone()[0]

            if has_attempts:
                flash(
                    "This student has existing test attempts and cannot "
                    "be deleted. Disable the account instead.",
                    "error"
                )
                return redirect(url_for("lecturer.lecturer_management_route"))

            # Delete the user. The associated student profile is deleted
            # automatically through ON DELETE CASCADE.
            cur.execute("""
                DELETE FROM users
                WHERE user_id = %s
                  AND role = 'student'
                RETURNING first_name, last_name;
            """, (student_id,))

            deleted_user = cur.fetchone()

        if deleted_user:
            flash(
                f"Account for {deleted_user[0]} {deleted_user[1]} deleted.",
                "success"
            )
        else:
            flash("Student account not found.", "error")

    except psycopg.errors.ForeignKeyViolation:
        flash(
            "The student cannot be deleted because related records exist.",
            "error"
        )

    except psycopg.Error:
        flash("A database error occurred while deleting the student.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))