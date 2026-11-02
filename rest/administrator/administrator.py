import json
import math
import os

from pathlib import Path
from datetime import datetime
from flask import render_template, request, redirect, url_for

# Data file path for subjects JSON

DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "subjects.json"
)

# Load subjects from JSON file
def load_subjects():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("subjects", [])

def save_subjects(subjects):

    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_file = DATA_FILE.with_suffix(".tmp")

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
        os.replace(temp_file, DATA_FILE)

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
        "name": subject.get("name", ""),
        "code": subject.get("code", ""),
        "description": subject.get("description", "")
    }

    # Error handling
    errors = {}
    general_error = None

    if request.method == "POST":

        form_data = {
            "name": request.form.get("name", "").strip(),
            "code": request.form.get("code", "").strip(),
            "description": request.form.get("description", "").strip()
        }

        # ------------------------------------------
        # DATABASE UPDATE PLACEHOLDER
        # ------------------------------------------
        #
        # Eventually, your database function should
        # return a result in this format:
        #
        # {
        #     "success": False,
        #     "message": "Check the highlighted fields.",
        #     "errors": {
        #         "code": "This code is already in use."
        #     }
        # }
        #
        # ------------------------------------------

        # Temporary JSON validation
        if not form_data["name"]:
            errors["name"] = "Subject name is required."

        if not form_data["code"]:
            errors["code"] = "Unique code is required."

        if not form_data["description"]:
            errors["description"] = "Description is required."

        if not errors:

            duplicate_code = any(
                item.get("code", "").lower() == form_data["code"].lower()
                and item.get("subjectId") != subject_id
                for item in subjects
            )

            if duplicate_code:
                errors["code"] = (
                    f"This code is already used by "
                    f"{next(
                        item['name'] for item in subjects
                        if item.get('code', '').lower() == form_data['code'].lower()
                        and item.get('subjectId') != subject_id
                    )}. Enter a unique code."
                )

        # Process form submission if no errors

        if errors:

            general_error = "Check the highlighted fields"

        else:

            # Update subject
            subject["name"] = form_data["name"]
            subject["code"] = form_data["code"]
            subject["description"] = form_data["description"]

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
        form_data=form_data,
        updated_at=updated_at,
        errors=errors,
        general_error=general_error
    )

