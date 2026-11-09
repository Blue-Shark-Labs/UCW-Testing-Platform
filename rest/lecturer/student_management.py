import json
import os
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")

# Points to CSD_Assignment/data/users.json
DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "users.json"


def load_users():
    if not DATA_FILE.exists():
        print(f"[ERROR] JSON file not found at: {DATA_FILE}")
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("users", [])
    except Exception as e:
        print(f"[ERROR] Failed to read JSON file: {e}")
        return []


def save_users(users):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = DATA_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump({"users": users}, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_file, DATA_FILE)
        return True
    except (OSError, TypeError, ValueError) as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False


@lecturer_bp.route("/student-management", methods=["GET"])
def lecturer_management_route():
    all_users = load_users()

    # DEBUG PRINTS - Check your Terminal where Flask is running:
    print(f"\n--- DEBUG: Loading JSON ---")
    print(f"File Path: {DATA_FILE}")
    print(f"File Exists? {DATA_FILE.exists()}")
    print(f"Total Users Found in JSON: {len(all_users)}")
    if all_users:
        print(f"Sample User Roles: {[u.get('role') for u in all_users[:5]]}")
    print(f"---------------------------\n")

    # Case-insensitive role match
    students_raw = [u for u in all_users if u.get("role", "").lower() == "student"]
    print(f"Total 'student' roles found: {len(students_raw)}")

    # Case-insensitive role match for student accounts

    formatted_students = []
    for u in students_raw:
        is_approved = u.get("isApproved", True)
        is_disabled = u.get("isDisabled", False)

        if not is_approved:
            status = "Pending Approval"
        elif is_disabled:
            status = "Disabled"
        else:
            status = "Active"

        formatted_students.append({
            "student_id": str(u.get("userId")),
            "first_name": u.get("firstName", ""),
            "last_name": u.get("lastName", ""),
            "name": f"{u.get('firstName', '')} {u.get('lastName', '')}".strip(),
            "email": u.get("email", ""),
            "course": u.get("courseTitle", u.get("course", "General Studies")),
            "last_login": u.get("lastLoginAt", "Never"),
            "status": status,
            "is_approved": is_approved,
            "is_disabled": is_disabled
        })

    # Search filter
    search_query = request.args.get("q", "").strip().lower()
    if search_query:
        formatted_students = [
            s for s in formatted_students
            if search_query in s["name"].lower()
            or search_query in s["student_id"].lower()
            or search_query in s["course"].lower()
            or search_query in s["email"].lower()
        ]

    stats = {
        "total_students": len(students_raw),
        "pending_approvals": sum(1 for s in students_raw if not s.get("isApproved", True)),
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


@lecturer_bp.route("/student/<student_id>/approve", methods=["POST"])
def approve_student_route(student_id):
    users = load_users()
    user = next((u for u in users if str(u.get("userId")) == str(student_id)), None)

    if user:
        user["isApproved"] = True
        user["isDisabled"] = False
        if save_users(users):
            flash(f"Account for {user.get('firstName')} {user.get('lastName')} approved.", "success")
        else:
            flash("Error saving user changes.", "error")
    else:
        flash("Student record not found.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


@lecturer_bp.route("/student/<student_id>/toggle-status", methods=["POST"])
def toggle_student_status_route(student_id):
    users = load_users()
    user = next((u for u in users if str(u.get("userId")) == str(student_id)), None)

    if user:
        current_disabled = user.get("isDisabled", False)
        user["isDisabled"] = not current_disabled

        if save_users(users):
            action_word = "re-enabled" if current_disabled else "disabled"
            flash(f"Account for {user.get('firstName')} {user.get('lastName')} {action_word}.", "warning" if not current_disabled else "success")
        else:
            flash("Error saving user changes.", "error")
    else:
        flash("Student record not found.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


@lecturer_bp.route("/student/<student_id>/delete", methods=["POST"])
def delete_student_route(student_id):
    users = load_users()
    user = next((u for u in users if str(u.get("userId")) == str(student_id)), None)

    if user:
        updated_users = [u for u in users if str(u.get("userId")) != str(student_id)]
        if save_users(updated_users):
            flash(f"Account for {user.get('firstName')} {user.get('lastName')} deleted.", "error")
        else:
            flash("Error deleting user.", "error")
    else:
        flash("Student record not found.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))


@lecturer_bp.route("/student/<student_id>/edit", methods=["POST"])
def edit_student_route(student_id):
    users = load_users()
    user = next((u for u in users if str(u.get("userId")) == str(student_id)), None)

    if user:
        user["firstName"] = request.form.get("first_name", user.get("firstName", "")).strip()
        user["lastName"] = request.form.get("last_name", user.get("lastName", "")).strip()
        user["courseTitle"] = request.form.get("course", user.get("courseTitle", "")).strip()

        if save_users(users):
            flash(f"Updated record for {user.get('firstName')} {user.get('lastName')}.", "success")
        else:
            flash("Error updating user.", "error")
    else:
        flash("Student record not found.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))

@lecturer_bp.route("/student/create", methods=["POST"])
def create_student_route():
    users = load_users()

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()
    password = request.form.get("password", "Student123!").strip()

    if not first_name or not last_name or not email or not course:
        flash("All fields are required to create a student.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    # Check for email duplicates
    if any(u.get("email", "").lower() == email.lower() for u in users):
        flash(f"A user with email '{email}' already exists.", "error")
        return redirect(url_for("lecturer.lecturer_management_route"))

    # Generate next numeric userId
    existing_ids = [u.get("userId") for u in users if isinstance(u.get("userId"), int)]
    new_user_id = max(existing_ids, default=2000) + 1

    new_student = {
        "userId": new_user_id,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "passwordHash": password,
        "role": "student",
        "courseTitle": course,
        "isApproved": True,
        "isDisabled": False,
        "lastLoginAt": "Never"
    }

    users.append(new_student)
    if save_users(users):
        flash(f"Student {first_name} {last_name} created successfully (ID: {new_user_id}).", "success")
    else:
        flash("Error saving new student record.", "error")

    return redirect(url_for("lecturer.lecturer_management_route"))