import math
import uuid
from uuid import UUID

from flask import render_template, request, redirect, url_for
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from werkzeug.security import generate_password_hash

from database.administrator.subjects import (
    create_subject,
    get_subject,
    list_available_lecturers,
    list_subjects,
    update_subject,
)
from database.administrator.users import (
    create_user,
    delete_user,
    get_user,
    list_users,
    set_user_disabled,
    update_user,
)


def _pagination(total, page, per_page=8):
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return page, start, {
        "page": page,
        "per_page": per_page,
        "total": total,
        "first": start + 1 if total else 0,
        "last": min(start + per_page, total),
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_num": page - 1,
        "next_num": page + 1,
    }


def _lecturer_selection(available_lecturers, submitted_ids):
    lecturers_by_id = {
        lecturer["userId"]: lecturer for lecturer in available_lecturers
    }
    lecturer_ids = []
    selected_lecturers = []
    valid = True

    for submitted_id in submitted_ids:
        try:
            lecturer_id = str(UUID(submitted_id))
        except ValueError:
            valid = False
            continue

        lecturer = lecturers_by_id.get(lecturer_id)
        if lecturer is None:
            valid = False
            continue

        if lecturer_id not in lecturer_ids:
            lecturer_ids.append(lecturer_id)
            selected_lecturers.append(lecturer)

    return lecturer_ids, selected_lecturers, valid

def administrator_view_subjects_route(methods=["GET"]):
    search = request.args.get("q", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 8
    subjects, total = list_subjects(search, per_page, (page - 1) * per_page)
    page, _, pagination = _pagination(total, page, per_page)
    if page != request.args.get("page", 1, type=int):
        subjects, total = list_subjects(search, per_page, (page - 1) * per_page)

    return render_template(
        "administrator/view_subjects.html",
        subjects=subjects,
        pagination=pagination,
        search=search
    )

def administrator_edit_subject_route(subject_id, methods=["GET", "POST"]):
    subject_id = UUID(str(subject_id))
    subject = get_subject(subject_id)
    if subject is None:
        return "Subject not found", 404

    all_available_lecturers = list_available_lecturers()
    form_data = {
        "isActive": subject["isActive"],
        "name": subject["name"],
        "description": subject["description"] or "",
        "lecturers": subject["lecturers"],
    }
    errors = {}
    general_error = None

    if request.method == "POST":
        submitted_status = request.form.get("isActive", "")
        status_values = {"true": True, "false": False}
        lecturer_ids, selected_lecturers, lecturers_valid = _lecturer_selection(
            all_available_lecturers,
            request.form.getlist("lecturerId"),
        )
        form_data = {
            "isActive": status_values.get(submitted_status, subject["isActive"]),
            "name": request.form.get("name", "").strip(),
            "subjectId": str(subject_id),
            "description": request.form.get("description", "").strip(),
            "lecturers": selected_lecturers,
        }

        if not form_data["name"]:
            errors["name"] = "Subject name is required."
        elif len(form_data["name"]) > 100:
            errors["name"] = "Subject name must be 100 characters or fewer."
        if not form_data["description"]:
            errors["description"] = "Description is required."
        elif len(form_data["description"]) > 250:
            errors["description"] = "Description must be 250 characters or fewer."
        if submitted_status not in status_values:
            errors["isActive"] = "Choose a valid subject status."
        if not lecturers_valid:
            errors["lecturers"] = "Choose valid lecturers."

        if errors:
            general_error = "Check the highlighted fields"
        else:
            try:
                updated = update_subject(
                    subject_id,
                    form_data["name"],
                    form_data["description"],
                    form_data["isActive"],
                    [UUID(lecturer_id) for lecturer_id in lecturer_ids],
                )
            except ValueError as error:
                errors["lecturers"] = str(error)
                general_error = "Check the highlighted fields"
            else:
                if updated:
                    return redirect(
                        url_for("administrator.administrator_view_subjects_route")
                    )
                return "Subject not found", 404

    return render_template(
        "administrator/edit_subject.html",
        subject=subject,
        all_available_lecturers=all_available_lecturers,
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )

def administrator_create_subject_route(methods=["GET", "POST"]):
    all_available_lecturers = list_available_lecturers()
    errors = {}
    general_error = None

    form_data = {
        "name": "",
        "subjectId": str(uuid.uuid4()),
        "description": "",
        "lecturers": [],
    }

    if request.method == "POST":
        subject_id = uuid.uuid4()

        lecturer_ids, selected_lecturers, lecturers_valid = _lecturer_selection(
            all_available_lecturers,
            request.form.getlist("lecturerId"),
        )
        form_data = {
            "name": request.form.get("name", "").strip(),
            "subjectId": str(subject_id),
            "description": request.form.get("description", "").strip(),
            "lecturers": selected_lecturers,
        }

        if not form_data["name"]:
            errors["name"] = "Subject name is required."
        elif len(form_data["name"]) > 100:
            errors["name"] = "Subject name must be 100 characters or fewer."
        if not form_data["description"]:
            errors["description"] = "Description is required."
        elif len(form_data["description"]) > 250:
            errors["description"] = "Description must be 250 characters or fewer."
        if not lecturers_valid:
            errors["lecturers"] = "Choose valid lecturers."

        if errors:
            general_error = "Check the highlighted fields"
        else:
            try:
                create_subject(
                    form_data["name"],
                    form_data["description"],
                    [UUID(lecturer_id) for lecturer_id in lecturer_ids],
                    subject_id,
                )
            except ValueError as error:
                errors["lecturers"] = str(error)
                general_error = "Check the highlighted fields"
            else:
                return redirect(
                    url_for("administrator.administrator_view_subjects_route")
                )

    return render_template(
        "administrator/create_subject.html",
        all_available_lecturers=all_available_lecturers,
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )

def administrator_view_users_route(methods=["GET"]):
    search = request.args.get("q", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 8
    users, total = list_users(search, per_page, (page - 1) * per_page)
    requested_page = page
    page, start, pagination = _pagination(total, page, per_page)
    if page != requested_page:
        users, total = list_users(search, per_page, start)

    return render_template(
        "administrator/view_users.html",
        users=users,
        pagination=pagination,
        search=search
    )

def administrator_activate_deactivate_user_route(user_id, action, methods=["GET"]):
    if action not in {"activate", "deactivate"}:
        return "Invalid account action", 400
    if not set_user_disabled(user_id, action == "deactivate"):
        return "User not found", 404
    return redirect(url_for("administrator.administrator_view_users_route"))


def administrator_edit_user_route(user_id, methods=["GET", "POST", "DELETE"]):
    user = get_user(user_id)
    if user is None:
        return "User not found", 404

    form_data = {
        "firstName": user["firstName"],
        "lastName": user["lastName"],
        "email": user["email"],
        "role": user["role"],
        "lastLoginAt": user["lastLoginAt"],
        "studentNumber": user["studentNumber"],
        "courseTitle": user["courseTitle"],
    }

    errors = {}
    general_error = None

    if request.method == "POST":
        form_data = {
            "firstName": request.form.get("firstName", "").strip(),
            "lastName": request.form.get("lastName", "").strip(),
            "email": request.form.get("email", "").strip(),
            "role": request.form.get("role", "").strip(),
            "lastLoginAt": user["lastLoginAt"],
            "studentNumber": request.form.get("studentNumber", "").strip(),
            "courseTitle": request.form.get("courseTitle", "").strip(),
        }

        if not form_data["firstName"]:
            errors["firstName"] = "First name is required."
        elif len(form_data["firstName"]) > 50:
            errors["firstName"] = "First name must be 50 characters or fewer."

        if not form_data["lastName"]:
            errors["lastName"] = "Last name is required."
        elif len(form_data["lastName"]) > 50:
            errors["lastName"] = "Last name must be 50 characters or fewer."

        if not form_data["email"]:
            errors["email"] = "Email is required."
        elif len(form_data["email"]) > 50 or "@" not in form_data["email"]:
            errors["email"] = "Enter a valid email address (maximum 50 characters)."

        if form_data["role"] not in {"student", "lecturer", "admin"}:
            errors["role"] = "Choose a valid user role."

        if form_data["role"] == "student":
            if not form_data["studentNumber"]:
                errors["studentNumber"] = "Student number is required."
            elif len(form_data["studentNumber"]) > 20:
                errors["studentNumber"] = "Student number must be 20 characters or fewer."
            if not form_data["courseTitle"]:
                errors["courseTitle"] = "Course title is required."
            elif len(form_data["courseTitle"]) > 100:
                errors["courseTitle"] = "Course title must be 100 characters or fewer."

        if not errors:
            try:
                updated = update_user(
                    user_id,
                    form_data["firstName"],
                    form_data["lastName"],
                    form_data["email"],
                    form_data["role"],
                    form_data["studentNumber"] or None,
                    form_data["courseTitle"] or None,
                )
            except UniqueViolation:
                errors["email"] = "A user with this email already exists."
                general_error = "Check the highlighted fields"
            else:
                if not updated:
                    return "User not found", 404
                return redirect(url_for("administrator.administrator_view_users_route"))

        if errors:
            general_error = "Check the highlighted fields"

    if request.method == "DELETE":
        try:
            deleted = delete_user(user_id)
        except ForeignKeyViolation:
            return (
                "This user is referenced by tests or attempts and cannot be deleted.",
                409,
            )
        if deleted:
            return "", 204
        return "User not found", 404

    return render_template(
        "administrator/edit_user.html",
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )

def administrator_create_user_route(methods=["GET", "POST"]):
    form_data = {
        "firstName": "",
        "lastName": "",
        "email": "",
        "role": "lecturer",
        "studentNumber": "",
        "courseTitle": "",
    }

    errors = {}
    general_error = None

    if request.method == "POST":
        form_data = {
            "firstName": request.form.get("firstName", "").strip(),
            "lastName": request.form.get("lastName", "").strip(),
            "email": request.form.get("email", "").strip(),
            "role": request.form.get("role", "").strip(),
            "studentNumber": request.form.get("studentNumber", "").strip(),
            "courseTitle": request.form.get("courseTitle", "").strip(),
        }
        password = request.form.get("password", "")

        if not form_data["firstName"]:
            errors["firstName"] = "First name is required."
        elif len(form_data["firstName"]) > 50:
            errors["firstName"] = "First name must be 50 characters or fewer."
        if not form_data["lastName"]:
            errors["lastName"] = "Last name is required."
        elif len(form_data["lastName"]) > 50:
            errors["lastName"] = "Last name must be 50 characters or fewer."
        if not form_data["email"]:
            errors["email"] = "Email is required."
        elif len(form_data["email"]) > 50 or "@" not in form_data["email"]:
            errors["email"] = "Enter a valid email address (maximum 50 characters)."
        if form_data["role"] not in {"student", "lecturer", "admin"}:
            errors["role"] = "Choose a valid user role."
        if not password:
            errors["password"] = "Password is required."
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters."

        if form_data["role"] == "student":
            if not form_data["studentNumber"]:
                errors["studentNumber"] = "Student number is required."
            elif len(form_data["studentNumber"]) > 20:
                errors["studentNumber"] = "Student number must be 20 characters or fewer."
            if not form_data["courseTitle"]:
                errors["courseTitle"] = "Course title is required."
            elif len(form_data["courseTitle"]) > 100:
                errors["courseTitle"] = "Course title must be 100 characters or fewer."

        if errors:
            general_error = "Check the highlighted fields"
        else:
            try:
                create_user(
                    form_data["firstName"],
                    form_data["lastName"],
                    form_data["email"],
                    generate_password_hash(password),
                    form_data["role"],
                    form_data["studentNumber"] or None,
                    form_data["courseTitle"] or None,
                )
            except UniqueViolation:
                errors["email"] = "A user with this email already exists."
                general_error = "Check the highlighted fields"
            else:
                return redirect(url_for("administrator.administrator_view_users_route"))

    return render_template(
        "administrator/create_user.html",
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )
