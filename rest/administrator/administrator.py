import json
import math
import os
import uuid

from pathlib import Path
from datetime import datetime
from flask import render_template, request, redirect, url_for

# Data file path for subjects JSON

SUBJECTS_DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "subjects.json"
)

USERS_DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "users.json"
)

# Load subjects from JSON file
def load_subjects():
    if not SUBJECTS_DATA_FILE.exists():
        return []

    with open(SUBJECTS_DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("subjects", [])

# Load users from JSON file
def load_users():
    if not USERS_DATA_FILE.exists():
        return []

    with open(USERS_DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("users", [])

def save_users(users):
    USERS_DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_file = USERS_DATA_FILE.with_suffix(".tmp")

    try:

        # Write JSON to temporary file
        with open(temp_file, "w", encoding="utf-8") as file:

            json.dump(
                {"users": users},
                file,
                indent=4,
                ensure_ascii=False
            )

            file.flush()
            os.fsync(file.fileno())

        # Atomically replace original JSON file
        os.replace(temp_file, USERS_DATA_FILE)

        return True

    except (OSError, TypeError, ValueError):

        # Clean up temporary file if saving fails
        if temp_file.exists():
            temp_file.unlink()

        return False

def save_subjects(subjects):

    SUBJECTS_DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_file = SUBJECTS_DATA_FILE.with_suffix(".tmp")

    try:

        # Write JSON to temporary file
        with open(temp_file, "w", encoding="utf-8") as file:

            json.dump(
                {"subjects": subjects},
                file,
                indent=4,
                ensure_ascii=False
            )

            file.flush()
            os.fsync(file.fileno())

        # Atomically replace original JSON file
        os.replace(temp_file, SUBJECTS_DATA_FILE)

        return True

    except (OSError, TypeError, ValueError):

        # Clean up temporary file if saving fails
        if temp_file.exists():
            temp_file.unlink()

        return False

# View subjects route for the administrator

def administrator_view_subjects_route(methods=["GET"]):
    # Load subjects from JSON
    all_subjects = load_subjects()

    # Search
    search = request.args.get("q", "").strip().lower()

    if search:
        all_subjects = [
            subject for subject in all_subjects
            if search in subject.get("name", "").lower()
            or search in subject.get("description", "").lower()
        ]

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 8

    total = len(all_subjects)
    total_pages = max(
        1,
        math.ceil(total / per_page)
    )
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page

    paginated_subjects = all_subjects[start:end]

    lecturer_names_by_id = {
        user["userId"]: " ".join(
            name for name in (user.get("firstName"), user.get("lastName")) if name
        )
        for user in load_users()
        if user.get("role") == "lecturer" and user.get("userId") is not None
    }
    paginated_subjects = [
        {
            **subject,
            "lecturerNames": [
                lecturer_names_by_id[lecturer_id]
                for lecturer_id in subject.get("lecturers", [])
                if lecturer_id in lecturer_names_by_id
            ]
        }
        for subject in paginated_subjects
    ]

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "first": start + 1 if total else 0,
        "last": min(end, total),
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_num": page - 1,
        "next_num": page + 1
    }

    return render_template(
        "administrator/view_subjects.html",
        subjects=paginated_subjects,
        pagination=pagination,
        search=search
    )

def administrator_edit_subject_route(subject_id, methods=["GET", "POST"]):
    subjects = load_subjects()
    all_available_lecturers = [user for user in load_users() if user.get("role") == "lecturer" or user.get("role") == "admin"]
    subject_lecturers = next(
        (s.get("lecturers", []) for s in subjects if s.get("subjectId") == subject_id),
        []
    )
    subject_lecturers = [
        {
            "firstName": lecturer.get("firstName"),
            "lastName": lecturer.get("lastName"),
            "userId": lecturer.get("userId")
        }
        for lecturer in all_available_lecturers
        if lecturer.get("userId") in subject_lecturers
    ]

    subject = next(
        (
            item for item in subjects
            if item.get("subjectId") == subject_id
        ),
        None
    )

    if subject is None:
        return "Subject not found", 404

    # Preserve submitted values
    form_data = {
        "isActive": subject.get("isActive"),
        "name": subject.get("name", ""),
        "description": subject.get("description", ""),
        "lecturers": subject_lecturers
    }

    # Error handling
    errors = {}
    general_error = None

    if request.method == "POST":
        submitted_status = request.form.get("isActive")
        status_values = {"true": True, "false": False}
        form_data = {
            "isActive": status_values.get(submitted_status),
            "name": request.form.get("name", "").strip(),
            "subjectId": subject_id,  # Code is not editable
            "description": request.form.get("description", "").strip(),
            "lecturers":  [int(id) for id in request.form.getlist("lecturerId")]  # List of selected lecturers
        }

        # Temporary JSON validation
        if not form_data["name"]:
            errors["name"] = "Subject name is required."

        if not form_data["description"]:
            errors["description"] = "Description is required."

        # Process form submission if no errors

        if errors:

            general_error = "Check the highlighted fields"

        else:

            # Update subject
            subject["isActive"] = form_data["isActive"]
            subject["name"] = form_data["name"]
            subject["subjectId"] = subject_id  # Code is not editable
            subject["description"] = form_data["description"]
            subject["lecturers"] = form_data["lecturers"]
            subject["updatedAt"] = datetime.now().strftime("%Y-%m-%d")

            if save_subjects(subjects):

                return redirect(
                    url_for("administrator.administrator_view_subjects_route")
                )

            else:

                general_error = "Unable to save subject. Please try again."

    # Format last updated date
    updated_at = subject.get("updatedAt", "")

    if updated_at:
        try:
            updated_at = datetime.strptime(
                updated_at, "%Y-%m-%d"
            ).strftime("%d %b %Y")
        except ValueError:
            pass

    return render_template(
        "administrator/edit_subject.html",
        subject=subject,
        all_available_lecturers=all_available_lecturers,
        form_data=form_data,
        updated_at=updated_at,
        errors=errors,
        general_error=general_error
    )

def administrator_create_subject_route(methods=["GET", "POST"]):
    all_available_lecturers = [user for user in load_users() if user.get("role") == "lecturer" or user.get("role") == "admin"]
    errors = {}
    general_error = None

    form_data = {
        "name": "",
        "subjectId": str(uuid.uuid4()),
        "description": "",
        "lecturers":  [],  # List of selected lecturers
    }

    if request.method == "POST":
        form_data = {
            "isActive": True,
            "name": request.form.get("name", "").strip(),
            "subjectId": request.form.get("subjectId", "").strip(),
            "description": request.form.get("description", "").strip(),
            "lecturers":  [int(id) for id in request.form.getlist("lecturerId")],  # List of selected lecturers
            "updatedAt": datetime.now().strftime("%Y-%m-%d")
        }

        if not form_data["subjectId"]:
            form_data["subjectId"] = str(uuid.uuid4())

        if not form_data["name"]:
            errors["name"] = "Subject name is required."

        if not form_data["description"]:
            errors["description"] = "Description is required."

        if errors:
            general_error = "Check the highlighted fields"
        else:
            subjects = load_subjects()
            subjects.append(form_data)

            if save_subjects(subjects):
                return redirect(
                    url_for("administrator.administrator_view_subjects_route")
                )

            general_error = "Unable to save subject. Please try again."

    return render_template(
        "administrator/create_subject.html",
        all_available_lecturers=all_available_lecturers,
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )

def administrator_view_users_route(methods=["GET"]):
    all_users = load_users()

    #search = request.args.get("q", "").strip().lower()
    search = ""

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 8

    total = len(all_users)
    total_pages = max(
        1,
        math.ceil(total / per_page)
    )
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page

    paginated_users = all_users[start:end]

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "first": start + 1 if total else 0,
        "last": min(end, total),
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_num": page - 1,
        "next_num": page + 1
    }
    
    return render_template(
    "administrator/view_users.html",
    users=paginated_users,
    pagination=pagination,
    search=search
    )

def administrator_activate_deactivate_user_route(user_id, action, methods=["GET"]):
    all_users = load_users()

    user = next((u for u in all_users if u["userId"] == user_id), None)

    if user:
        if action == "activate":
            user["isDisabled"] = False
        elif action == "deactivate":
            user["isDisabled"] = True

        if save_users(all_users):
            return redirect(url_for("administrator.administrator_view_users_route"))
        else:
            return "Failed to update user status", 500


def administrator_edit_user_route(user_id, methods=["GET", "POST", "DELETE"]):
    all_users = load_users()
    user = next(u for u in all_users if u["userId"] == user_id)

    form_data = {
        "firstName": user.get("firstName", ""),
        "lastName": user.get("lastName", ""),
        "email": user.get("email", ""),
        "role": user.get("role", ""),
        "lastLoginAt": user.get("lastLoginAt", "")
    }

    errors = {}
    general_error = None

    if request.method == "POST":
        form_data = {
            "firstName": request.form.get("firstName", "").strip(),
            "lastName": request.form.get("lastName", "").strip(),
            "email": request.form.get("email", "").strip(),
            "role": request.form.get("role", "").strip(),
            "lastLoginAt": user.get("lastLoginAt", "")
        }

        errors = {}

        if not form_data["firstName"]:
            errors["firstName"] = "First name is required."

        if not form_data["lastName"]:
            errors["lastName"] = "Last name is required."

        if not form_data["email"]:
            errors["email"] = "Email is required."

        if not form_data["role"]:
            errors["role"] = "Role is required."

        if not errors:
            user.update(form_data)

            if save_users(all_users):
                return redirect(url_for("administrator.administrator_view_users_route"))
            else:
                general_error = "Unable to save user. Please try again."
        else:
            general_error = "Check the highlighted fields"

    if request.method == "DELETE":
        all_users = [u for u in all_users if u["userId"] != user_id]

        if save_users(all_users):
            return "", 204
        else:
            general_error = "Unable to delete user. Please try again."

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
        "lastLoginAt": "n/a"
    }

    errors = {}
    general_error = None

    if request.method == "POST":
        users = load_users()

        form_data = {
            "userId": max(
                (user["userId"] for user in users),
                default=1000
            ) + 1,
            "firstName": request.form.get("firstName", "").strip(),
            "lastName": request.form.get("lastName", "").strip(),
            "email": request.form.get("email", "").strip(),
            "passwordHash": "REPLACE_WITH_BCRYPT_HASH",
            "role": request.form.get("role", "").strip(),
            "mfaEnabled": False,
            "mfaSecret": None,
            "isDisabled": True,
            "lastLoginAt": None
        }

        try:
            users.append(form_data)
            if save_users(users):
                return redirect(url_for("administrator.administrator_view_users_route"))

            general_error = "Unable to save user due to connection. Please try again."
            return render_template(
                "administrator/create_user.html",
                form_data=form_data,
                errors=errors,
                general_error=general_error
            )
        except:
            general_error = "Oops, you've dropped a clanger"
            return render_template(
                "administrator/create_user.html",
                form_data=form_data,
                errors=errors,
                general_error=general_error
            )

    return render_template(
        "administrator/create_user.html",
        form_data=form_data,
        errors=errors,
        general_error=general_error
    )
