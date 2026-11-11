from flask import Blueprint, render_template, request, redirect, url_for, flash

test_management_bp = Blueprint("lecturer_tests", __name__, url_prefix="/lecturer")

# Mock data store for tests matching UCW requirements
MOCK_TESTS = [
    {
        "test_id": "TST-101",
        "title": "Marine Ecosystems Midterm",
        "subject": "Ocean Science",
        "question_count": 15,
        "time_limit": 30,  # minutes
        "attempts": 24,
        "status": "Active"
    },
    {
        "test_id": "TST-102",
        "title": "Pelagic Habitats Quiz 1",
        "subject": "Pelagic Ecology",
        "question_count": 10,
        "time_limit": 15,  # minutes
        "attempts": 0,
        "status": "Active"
    },
    {
        "test_id": "TST-103",
        "title": "Data Structures Diagnostic",
        "subject": "Computer Science",
        "question_count": 20,
        "time_limit": None,  # No limit
        "attempts": 5,
        "status": "Draft"
    }
]

SUBJECTS = ["Ocean Science", "Pelagic Ecology", "Computer Science", "Marine Biology"]


@test_management_bp.route("test-management", methods=["GET"])
def test_management_route():
    search_query = request.args.get("q", "").strip().lower()
    subject_filter = request.args.get("subject", "").strip()

    filtered_tests = MOCK_TESTS
    if search_query:
        filtered_tests = [
            t for t in filtered_tests
            if search_query in t["title"].lower()
            or search_query in t["test_id"].lower()
            or search_query in t["subject"].lower()
        ]

    if subject_filter:
        filtered_tests = [t for t in filtered_tests if t["subject"] == subject_filter]

    stats = {
        "total_tests": len(MOCK_TESTS),
        "active_tests": sum(1 for t in MOCK_TESTS if t["status"] == "Active"),
        "total_attempts": sum(t["attempts"] for t in MOCK_TESTS),
        "subject_count": len(SUBJECTS)
    }

    pagination = {
        "page": 1,
        "per_page": 10,
        "total": len(filtered_tests),
        "first": 1 if filtered_tests else 0,
        "last": len(filtered_tests),
        "total_pages": 1,
        "has_prev": False,
        "has_next": False,
        "prev_num": 1,
        "next_num": 1
    }

    return render_template(
        "lecturer/test_management.html",
        tests=filtered_tests,
        subjects=SUBJECTS,
        stats=stats,
        pagination=pagination,
        search=request.args.get("q", ""),
        selected_subject=subject_filter
    )


@test_management_bp.route("/create", methods=["POST"])
def create_test_route():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    time_limit_raw = request.form.get("time_limit", "").strip()
    question_count_raw = request.form.get("question_count", "10").strip()

    if not title or not subject:
        flash("Test title and subject are required.", "error")
        return redirect(url_for("lecturer_tests.test_management_route"))

    time_limit = int(time_limit_raw) if time_limit_raw and time_limit_raw.isdigit() else None
    question_count = int(question_count_raw) if question_count_raw.isdigit() else 10

    new_test_id = f"TST-{101 + len(MOCK_TESTS)}"
    new_test = {
        "test_id": new_test_id,
        "title": title,
        "subject": subject,
        "question_count": question_count,
        "time_limit": time_limit,
        "attempts": 0,
        "status": "Active"
    }

    MOCK_TESTS.append(new_test)
    flash(f"Test '{title}' ({new_test_id}) created successfully.", "success")
    return redirect(url_for("lecturer_tests.test_management_route"))


@test_management_bp.route("/<test_id>/edit", methods=["POST"])
def edit_test_route(test_id):
    test = next((t for t in MOCK_TESTS if t["test_id"] == test_id), None)
    if not test:
        flash("Test not found.", "error")
        return redirect(url_for("lecturer_tests.test_management_route"))

    test["title"] = request.form.get("title", test["title"]).strip()
    test["subject"] = request.form.get("subject", test["subject"]).strip()

    time_limit_raw = request.form.get("time_limit", "").strip()
    test["time_limit"] = int(time_limit_raw) if time_limit_raw and time_limit_raw.isdigit() else None

    question_count_raw = request.form.get("question_count", "").strip()
    if question_count_raw and question_count_raw.isdigit():
        test["question_count"] = int(question_count_raw)

    test["status"] = request.form.get("status", test["status"])

    flash(f"Test '{test['title']}' updated.", "success")
    return redirect(url_for("lecturer_tests.test_management_route"))


@test_management_bp.route("/<test_id>/delete", methods=["POST"])
def delete_test_route(test_id):
    global MOCK_TESTS
    test = next((t for t in MOCK_TESTS if t["test_id"] == test_id), None)
    if not test:
        flash("Test not found.", "error")
        return redirect(url_for("lecturer_tests.test_management_route"))

    confirmed = request.form.get("confirmed", "false") == "true"

    if test["attempts"] > 0 and not confirmed:
        flash(f"Cannot delete '{test['title']}': student attempts exist. Confirm deletion in the prompt.", "warning")
        return redirect(url_for("lecturer_tests.test_management_route"))

    MOCK_TESTS = [t for t in MOCK_TESTS if t["test_id"] != test_id]
    flash(f"Test '{test['title']}' permanently deleted.", "error")
    return redirect(url_for("lecturer_tests.test_management_route"))