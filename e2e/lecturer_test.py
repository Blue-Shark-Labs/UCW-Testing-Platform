from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timezone
import re
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import psycopg
import pytest
from playwright.sync_api import Page, expect


LECTURER_ID = "00000000-0000-4000-8000-000000000010"
STUDENT_1_ID = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
STUDENT_2_ID = UUID("9e80f93c-ea42-4348-8a25-dc54a68be6d2")
SUBJECT_1_ID = UUID("550e8400-e29b-41d4-a716-446655440001")
SUBJECT_2_ID = UUID("550e8400-e29b-41d4-a716-446655440002")
QUIZ_1_ID = UUID("22222222-2222-2222-2222-222222222222")
QUIZ_2_ID = UUID("22222222-2222-2222-2222-222222222223")
QUESTION_1_ID = UUID("33333333-3333-3333-3333-333333333333")
QUESTION_2_ID = UUID("33333333-3333-3333-3333-333333333334")


def safe_click(locator) -> None:
    locator.evaluate("el => el.scrollIntoView({ block: 'center', inline: 'center' })")
    locator.click()


@pytest.fixture
def lecturer_sign_in(sign_in):
    """Signs in as a lecturer and overrides rest.router's DB user lookup."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("Lee", "Lecturer", "lecturer", False)
    mock_provider = MagicMock()
    mock_provider.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("rest.router.PostgresConnectionProvider", mock_provider):
        sign_in(role="lecturer")
        yield


@pytest.fixture
def admin_sign_in(sign_in):
    """Signs in as an admin to verify admin access to the lecturer portal."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("Ada", "Admin", "admin", False)
    mock_provider = MagicMock()
    mock_provider.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("rest.router.PostgresConnectionProvider", mock_provider):
        sign_in(role="admin")
        yield

@pytest.fixture
def lecturer_state():
    """Stateful in-memory data store backing all lecturer routes during E2E tests."""
    state = {
        "students": [
            [
                STUDENT_1_ID,
                "Sam",
                "Student",
                "sam@dev.local",
                datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc),
                False,
                "S0000001",
                "BSc Computer Science",
                True,
            ],
            [
                STUDENT_2_ID,
                "Alex",
                "Pending",
                "alex@dev.local",
                None,
                False,
                "S0000002",
                "BSc Computing",
                False,
            ],
        ],
        "quizzes": [
            {
                "test_id": str(QUIZ_1_ID),
                "subject_id": str(SUBJECT_1_ID),
                "subject_name": "Marine Biology",
                "title": "Reef Ecology Quiz",
                "description": "Introductory coral reef assessment",
                "question_count": 1,
                "time_limit_minutes": 15,
                "is_active": True,
                "attempt_count": 2,
            },
            {
                "test_id": str(QUIZ_2_ID),
                "subject_id": str(SUBJECT_2_ID),
                "subject_name": "Algorithms",
                "title": "Sorting Draft Quiz",
                "description": "Unattempted draft quiz",
                "question_count": 1,
                "time_limit_minutes": None,
                "is_active": False,
                "attempt_count": 0,
            },
        ],
        "questions": [
            {
                "question_id": str(QUESTION_1_ID),
                "subject_id": str(SUBJECT_1_ID),
                "subject_name": "Marine Biology",
                "question_text": "Which organism builds coral reefs?",
                "options": [
                    {"option_text": "Coral polyps", "is_correct": True},
                    {"option_text": "Kelp", "is_correct": False},
                ],
            },
            {
                "question_id": str(QUESTION_2_ID),
                "subject_id": str(SUBJECT_2_ID),
                "subject_name": "Algorithms",
                "question_text": "What is the average time complexity of merge sort?",
                "options": [
                    {"option_text": "O(n log n)", "is_correct": True},
                    {"option_text": "O(n^2)", "is_correct": False},
                ],
            },
        ],
        "subjects": [
            {
                "subject_id": str(SUBJECT_1_ID),
                "name": "Marine Biology",
                "description": "Study of marine ecosystems and reef habitats",
                "is_active": True,
                "is_assigned": True,
                "lecturer_names": ["Lee Lecturer"],
                "question_count": 1,
                "quiz_count": 1,
            },
            {
                "subject_id": str(SUBJECT_2_ID),
                "name": "Algorithms",
                "description": "Data structures and complexity analysis",
                "is_active": True,
                "is_assigned": False,
                "lecturer_names": ["Dr. Ada"],
                "question_count": 1,
                "quiz_count": 1,
            },
        ],
    }

    def sync_subject_counts():
        for subj in state["subjects"]:
            sid = subj["subject_id"]
            subj["question_count"] = sum(
                1 for q in state["questions"] if q["subject_id"] == sid
            )
            subj["quiz_count"] = sum(
                1 for qz in state["quizzes"] if qz["subject_id"] == sid
            )

    def _subject_name(subject_id: UUID | str) -> str:
        sid = str(subject_id)
        for subj in state["subjects"]:
            if subj["subject_id"] == sid:
                return subj["name"]
        return "Unknown Subject"

    # --- Dashboard helpers ---
    def mock_dashboard_overview(lecturer_id):
        pending = [
            {
                "student_id": str(s[0]),
                "name": f"{s[1]} {s[2]}",
                "student_number": s[6],
                "email": s[3],
                "course_title": s[7],
            }
            for s in state["students"]
            if s[6] is not None and not s[8]
        ]
        return {
            "stats": {
                "assigned_subjects_count": 1,
                "total_students": len(state["students"]),
                "pending_approvals": len(pending),
                "active_quizzes": sum(1 for q in state["quizzes"] if q["is_active"]),
                "total_quizzes": len(state["quizzes"]),
                "total_questions": len(state["questions"]),
                "completed_attempts": 2,
                "class_average": "85.0%",
            },
            "pending_students": pending,
            "assigned_subjects": [s for s in state["subjects"] if s["is_assigned"]],
            "recent_quizzes": state["quizzes"],
        }

    # --- Student management helpers ---
    def mock_list_students():
        return list(state["students"])

    def mock_approve_student(student_id):
        for s in state["students"]:
            if str(s[0]) == str(student_id):
                s[8] = True
                return {"email": s[3], "first_name": s[1]}
        return None

    def mock_reject_student(student_id):
        for idx, s in enumerate(state["students"]):
            if str(s[0]) == str(student_id):
                if s[8]:
                    return "already_approved", None
                removed = state["students"].pop(idx)
                return "rejected", (removed[1], removed[2])
        return "not_found", None

    def mock_toggle_student_status(student_id):
        for s in state["students"]:
            if str(s[0]) == str(student_id):
                s[5] = not s[5]
                return s[5]
        return None

    def mock_update_student(student_id, first_name, last_name, course):
        for s in state["students"]:
            if str(s[0]) == str(student_id):
                s[1] = first_name
                s[2] = last_name
                s[7] = course
                return True
        return False

    def mock_create_student(first_name, last_name, email, password_hash, course):
        if any(s[3].lower() == email.lower() for s in state["students"]):
            raise psycopg.errors.UniqueViolation("Duplicate email")
        new_num = f"S{len(state['students']) + 1:07d}"
        state["students"].append([
            uuid4(),
            first_name,
            last_name,
            email,
            None,
            False,
            new_num,
            course,
            True,
        ])
        return new_num

    def mock_delete_student(student_id):
        for idx, s in enumerate(state["students"]):
            if str(s[0]) == str(student_id):
                if s[0] == STUDENT_1_ID:
                    s[1] = "Deleted"
                    s[2] = "User"
                    s[3] = f"deleted_{s[0]}@anonymised.local"
                    s[5] = True
                    return "anonymised", ("Sam", "Student")
                removed = state["students"].pop(idx)
                return "deleted", (removed[1], removed[2])
        return "not_found", None

    # --- Student progress helpers ---
    def mock_class_progress():
        return [
            {
                "student_id": str(s[0]),
                "name": f"{s[1]} {s[2]}",
                "student_number": s[6],
                "email": s[3],
                "course_title": s[7],
                "completed_tests": 2 if s[0] == STUDENT_1_ID else 0,
                "cumulative_points": 210 if s[0] == STUDENT_1_ID else 0,
                "average_percentage": 85.0 if s[0] == STUDENT_1_ID else None,
            }
            for s in state["students"]
            if s[8]
        ]

    def mock_student_detail(student_id):
        if str(student_id) != str(STUDENT_1_ID):
            return None
        return {
            "student": {
                "student_id": str(STUDENT_1_ID),
                "name": "Sam Student",
                "student_number": "S0000001",
                "course_title": "BSc Computer Science",
                "email": "sam@dev.local",
                "cumulative_points": 210,
                "average_percentage": 85.0,
            },
            "trajectory": [
                {
                    "test_name": "Reef Ecology Quiz",
                    "percentage": 85.0,
                    "short_date_str": "18 Nov",
                }
            ],
            "history": [
                {
                    "test_name": "Reef Ecology Quiz",
                    "subject_name": "Marine Biology",
                    "completed_date_str": "18 Nov 2026, 09:15",
                    "question_count": 5,
                    "percentage": 85.0,
                    "total_points": 210,
                }
            ],
        }

    # --- Quiz & question pool helpers ---
    def mock_list_quizzes():
        return list(state["quizzes"])

    def mock_list_questions():
        return list(state["questions"])

    def mock_subjects_with_counts():
        sync_subject_counts()
        return [
            {
                "subject_id": s["subject_id"],
                "name": s["name"],
                "question_count": s["question_count"],
            }
            for s in state["subjects"]
        ]

    def mock_create_quiz(
        subject_id, created_by, title, description, question_count, time_limit_minutes
    ):
        pool_size = sum(
            1 for q in state["questions"] if q["subject_id"] == str(subject_id)
        )
        if question_count > pool_size:
            raise ValueError(
                f"Cannot sample {question_count} questions; pool only has {pool_size}."
            )
        new_id = str(uuid4())
        state["quizzes"].append({
            "test_id": new_id,
            "subject_id": str(subject_id),
            "subject_name": _subject_name(subject_id),
            "title": title,
            "description": description,
            "question_count": question_count,
            "time_limit_minutes": time_limit_minutes,
            "is_active": True,
            "attempt_count": 0,
        })
        sync_subject_counts()
        return new_id

    def mock_update_quiz(
        test_id, subject_id, title, description, question_count, time_limit_minutes
    ):
        for qz in state["quizzes"]:
            if qz["test_id"] == str(test_id):
                qz["title"] = title
                qz["description"] = description
                if qz["attempt_count"] == 0:
                    qz["subject_id"] = str(subject_id)
                    qz["subject_name"] = _subject_name(subject_id)
                    qz["question_count"] = question_count
                    qz["time_limit_minutes"] = time_limit_minutes
                sync_subject_counts()
                return True, None
        return False, "Quiz not found."

    def mock_toggle_quiz_status(test_id):
        for qz in state["quizzes"]:
            if qz["test_id"] == str(test_id):
                qz["is_active"] = not qz["is_active"]
                return qz["is_active"]
        return None

    def mock_delete_quiz(test_id, confirmed_archive):
        for idx, qz in enumerate(state["quizzes"]):
            if qz["test_id"] == str(test_id):
                if qz["attempt_count"] > 0:
                    if not confirmed_archive:
                        return "requires_confirmation", qz["title"]
                    qz["is_active"] = False
                    return "archived", qz["title"]
                removed = state["quizzes"].pop(idx)
                sync_subject_counts()
                return "deleted", removed["title"]
        return "not_found", None

    def mock_create_question(subject_id, question_text, options):
        state["questions"].append({
            "question_id": str(uuid4()),
            "subject_id": str(subject_id),
            "subject_name": _subject_name(subject_id),
            "question_text": question_text,
            "options": [
                {"option_text": text, "is_correct": is_correct}
                for text, is_correct in options
            ],
        })
        sync_subject_counts()

    def mock_update_question(question_id, subject_id, question_text, options):
        for item in state["questions"]:
            if item["question_id"] == str(question_id):
                item["subject_id"] = str(subject_id)
                item["subject_name"] = _subject_name(subject_id)
                item["question_text"] = question_text
                item["options"] = [
                    {"option_text": text, "is_correct": is_correct}
                    for text, is_correct in options
                ]
                sync_subject_counts()
                return True
        return False

    def mock_delete_question(question_id):
        for idx, item in enumerate(state["questions"]):
            if item["question_id"] == str(question_id):
                state["questions"].pop(idx)
                sync_subject_counts()
                return True
        return False

    def mock_quiz_statistics(test_id):
        if str(test_id) != str(QUIZ_1_ID):
            return None
        return {
            "quiz": state["quizzes"][0],
            "summary": {
                "completed_count": 2,
                "avg_percentage": 80.0,
                "avg_points": 160,
                "lowest_percentage": 70.0,
                "highest_percentage": 90.0,
            },
            "attempts": [
                {
                    "student_name": "Sam Student",
                    "student_number": "S0000001",
                    "completed_at": "18 Nov 2026, 09:15",
                    "percentage": 80.0,
                    "total_points": 160,
                }
            ],
        }

    def mock_list_subjects(lecturer_id, search="", assigned_only=False):
        sync_subject_counts()
        results = list(state["subjects"])
        if assigned_only:
            results = [s for s in results if s["is_assigned"]]
        if search:
            term = search.lower()
            results = [
                s for s in results
                if term in s["name"].lower() or term in s["description"].lower()
            ]
        return results

    patches = [
        patch("rest.lecturer.dashboard.list_students", mock_list_students),
        patch("rest.lecturer.dashboard.list_quizzes", mock_list_quizzes),
        patch("rest.lecturer.dashboard.list_questions", mock_list_questions),
        patch("rest.lecturer.dashboard.list_lecturer_subjects", mock_list_subjects),
        patch("rest.lecturer.dashboard.get_class_progress_summary", mock_class_progress),
        patch("rest.lecturer.student_management.list_students", mock_list_students),
        patch("rest.lecturer.student_management.approve_student", mock_approve_student),
        patch("rest.lecturer.student_management.reject_student", mock_reject_student),
        patch("rest.lecturer.student_management.toggle_student_status", mock_toggle_student_status),
        patch("rest.lecturer.student_management.update_student", mock_update_student),
        patch("rest.lecturer.student_management.create_student", mock_create_student),
        patch("rest.lecturer.student_management.delete_student", mock_delete_student),
        patch("rest.lecturer.student_management.send_student_approval_email", return_value=True),
        patch("rest.lecturer.student_management.get_class_progress_summary", mock_class_progress),
        patch("rest.lecturer.student_management.get_student_progress_detail", mock_student_detail),
        patch("rest.lecturer.quiz_management.list_quizzes", mock_list_quizzes),
        patch("rest.lecturer.quiz_management.list_questions", mock_list_questions),
        patch("rest.lecturer.quiz_management.list_subjects_with_pool_counts", mock_subjects_with_counts),
        patch("rest.lecturer.quiz_management.create_quiz", mock_create_quiz),
        patch("rest.lecturer.quiz_management.update_quiz", mock_update_quiz),
        patch("rest.lecturer.quiz_management.toggle_quiz_status", mock_toggle_quiz_status),
        patch("rest.lecturer.quiz_management.delete_quiz", mock_delete_quiz),
        patch("rest.lecturer.quiz_management.create_question", mock_create_question),
        patch("rest.lecturer.quiz_management.update_question", mock_update_question),
        patch("rest.lecturer.quiz_management.delete_question", mock_delete_question),
        patch("rest.lecturer.quiz_management.get_quiz_statistics", mock_quiz_statistics),
        patch("rest.lecturer.view_subjects.list_lecturer_subjects", mock_list_subjects),
    ]

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield state

class TestLecturerAccessControl:
    def test_redirects_to_login_when_signed_out(self, page: Page):
        page.goto("/lecturer/dashboard")
        expect(page).to_have_url(re.compile(r"/login$"))

    def test_forbids_student_role_from_lecturer_portal(self, page: Page, sign_in):
        sign_in(role="student")
        response = page.goto("/lecturer/dashboard")
        assert response is not None
        assert response.status == 403

    def test_allows_admin_role_to_access_lecturer_portal(
        self, page: Page, admin_sign_in, lecturer_state
    ):
        page.goto("/lecturer/dashboard")
        expect(page.get_by_role("heading", name="Lecturer Dashboard")).to_be_visible()
        expect(page.get_by_text("Welcome back, Ada Admin.")).to_be_visible()

class TestLecturerDashboardPage:
    def test_renders_overview_and_approves_pending_student(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/dashboard")

        expect(page.get_by_role("heading", name="Lecturer Dashboard")).to_be_visible()
        expect(page.get_by_text("Welcome back, Lee Lecturer.")).to_be_visible()
        expect(page.get_by_text("Alex Pending")).to_be_visible()
        expect(page.get_by_text("Reef Ecology Quiz")).to_be_visible()

        safe_click(page.get_by_role("button", name="Approve"))

        expect(page).to_have_url(re.compile(r"/lecturer/student-management$"))
        expect(page.get_by_role("status")).to_contain_text(
            "Student approved and confirmation email sent to alex@dev.local."
        )


class TestLecturerSubjectsPage:
    def test_filters_by_assigned_toggle_and_live_search(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/subjects")

        expect(page.get_by_role("heading", name="Subjects", exact=True)).to_be_visible()
        expect(page.get_by_text("Marine Biology")).to_be_visible()
        expect(page.get_by_text("Algorithms")).to_be_visible()

        # Live search narrows down rows without reload
        search_box = page.get_by_label("Search by name or description")
        search_box.fill("Algorithms")
        expect(page.get_by_text("Algorithms")).to_be_visible()
        expect(page.get_by_text("Marine Biology")).to_be_hidden()

        # Non-matching query displays empty state row
        search_box.fill("Nonexistent Subject")
        expect(page.get_by_text("No subjects match your search criteria.")).to_be_visible()
        search_box.fill("")

        # Toggle "Assigned to Me" query filter
        safe_click(page.get_by_role("link", name="Assigned to Me"))

        expect(page).to_have_url(re.compile(r"/lecturer/subjects\?.*assigned=1"))
        expect(page.get_by_text("Marine Biology")).to_be_visible()
        expect(page.get_by_text("Algorithms")).to_have_count(0)


class TestLecturerStudentManagementPage:
    def test_searches_filters_pending_and_edits_student_via_modal(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-management")

        expect(page.get_by_role("heading", name="Student Management")).to_be_visible()
        expect(page.get_by_text("Sam Student")).to_be_visible()
        expect(page.get_by_text("Alex Pending")).to_be_visible()

        # Toggle Pending Approval filter
        safe_click(page.get_by_role("button", name=re.compile(r"Pending Approval")))
        expect(page.get_by_text("Alex Pending")).to_be_visible()
        expect(page.get_by_text("Sam Student")).to_be_hidden()

        # Untoggle Pending Approval filter
        safe_click(page.get_by_role("button", name=re.compile(r"Pending Approval")))
        expect(page.get_by_text("Sam Student")).to_be_visible()

        # Live search by student ID
        search_box = page.get_by_label("Search by name or student ID")
        search_box.fill("S0000001")
        expect(page.get_by_text("Sam Student")).to_be_visible()
        expect(page.get_by_text("Alex Pending")).to_be_hidden()

        # Open Edit modal and update course
        safe_click(page.get_by_role("button", name="Edit details for Sam Student"))
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        dialog.locator("input[name='course']").fill("MSc Artificial Intelligence")
        dialog.get_by_role("button", name="Save Changes").click()

        expect(page.get_by_role("status")).to_contain_text("Updated record for Sam Student.")
        expect(page.get_by_text("MSc Artificial Intelligence")).to_be_visible()

    def test_reviews_and_approves_pending_student_via_modal(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-management")

        safe_click(page.get_by_role("button", name="Review registration request for Alex Pending"))

        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(dialog.get_by_text("Alex Pending")).to_be_visible()
        expect(dialog.get_by_text("S0000002")).to_be_visible()

        dialog.get_by_role("button", name="Approve").click()

        expect(page.get_by_role("status")).to_contain_text(
            "Student approved and confirmation email sent to alex@dev.local."
        )
        alex_row = page.locator("tr", has_text="Alex Pending")
        expect(alex_row.get_by_text("Active")).to_be_visible()

    def test_reviews_and_rejects_pending_student_via_modal(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-management")

        safe_click(page.get_by_role("button", name="Review registration request for Alex Pending"))

        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        dialog.get_by_role("button", name="Reject").click()

        expect(page.get_by_role("status")).to_contain_text(
            "Registration for Alex Pending rejected and removed."
        )
        expect(page.locator("table").get_by_text("Alex Pending")).to_have_count(0)

    def test_creates_student_and_blocks_duplicate_email(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-management")

        # Create valid student
        safe_click(page.get_by_role("button", name="Add New Student"))
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        dialog.locator("input[name='first_name']").fill("Jane")
        dialog.locator("input[name='last_name']").fill("Doe")
        dialog.locator("input[name='email']").fill("jane@dev.local")
        dialog.locator("input[name='course']").fill("BSc Marine Science")
        dialog.get_by_role("button", name="Add Student", exact=True).click()

        expect(page.get_by_role("status")).to_contain_text(
            "Student Jane Doe created successfully (Student Number: S0000003)."
        )
        expect(page.get_by_text("Jane Doe", exact=True)).to_be_visible()

        # Attempt to create with duplicate email
        safe_click(page.get_by_role("button", name="Add New Student"))
        dialog = page.get_by_role("dialog")
        dialog.locator("input[name='first_name']").fill("Duplicate")
        dialog.locator("input[name='last_name']").fill("User")
        dialog.locator("input[name='email']").fill("jane@dev.local")
        dialog.locator("input[name='course']").fill("BSc Marine Science")
        dialog.get_by_role("button", name="Add Student", exact=True).click()

        expect(page.get_by_role("status")).to_contain_text(
            "A user with email 'jane@dev.local' already exists."
        )

    def test_toggles_student_status_and_terminates_account(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-management")

        # Disable Sam Student
        safe_click(page.get_by_role("button", name="Disable account for Sam Student"))
        expect(page.get_by_role("status")).to_contain_text(
            "Student account disabled successfully."
        )
        sam_row = page.locator("tr", has_text="Sam Student")
        expect(sam_row.get_by_text("Disabled")).to_be_visible()

        # Re-enable Sam Student
        safe_click(page.get_by_role("button", name="Enable account for Sam Student"))
        expect(page.get_by_role("status")).to_contain_text(
            "Student account enabled successfully."
        )
        expect(sam_row.get_by_text("Active")).to_be_visible()

        # Terminate Sam Student (confirm browser dialog -> GDPR anonymisation)
        page.once("dialog", lambda dialog: dialog.accept())
        safe_click(page.get_by_role("button", name="Terminate account for Sam Student"))

        expect(page.get_by_role("status")).to_contain_text(
            "Account for Sam Student terminated and PII anonymised in compliance with GDPR"
        )
        expect(page.get_by_text("Deleted User")).to_be_visible()


class TestLecturerQuizManagementAndStats:
    def test_filters_by_subject_and_live_searches_quizzes(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/quiz-management")

        expect(page.get_by_text("Reef Ecology Quiz")).to_be_visible()
        expect(page.get_by_text("Sorting Draft Quiz")).to_be_visible()

        # Live search filter
        search_box = page.get_by_label("Search quizzes or questions")
        search_box.fill("Sorting")
        expect(page.get_by_text("Sorting Draft Quiz")).to_be_visible()
        expect(page.get_by_text("Reef Ecology Quiz")).to_be_hidden()
        search_box.fill("")

        # Subject dropdown filter
        page.get_by_label("Filter by subject").select_option(str(SUBJECT_1_ID))
        expect(page.get_by_text("Reef Ecology Quiz")).to_be_visible()
        expect(page.get_by_text("Sorting Draft Quiz")).to_have_count(0)

    def test_creates_edits_toggles_and_deletes_or_archives_quizzes(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/quiz-management")

        # 1. Client-side pool cap validation when question_count exceeds subject pool size
        safe_click(page.get_by_role("button", name="Create New Quiz"))
        dialog = page.get_by_role("dialog")
        dialog.locator("input[name='title']").fill("Oversized Quiz")
        dialog.locator("select[name='subject_id']").select_option(str(SUBJECT_1_ID))
        q_count_input = dialog.locator("input[name='question_count']")
        expect(q_count_input).to_have_attribute("max", "1")
        q_count_input.fill("5")
        dialog.get_by_role("button", name="Save Quiz").click()
        assert q_count_input.evaluate("el => el.validity.rangeOverflow") is True
        dialog.get_by_role("button", name="Cancel").click()

        # 2. Create valid quiz
        safe_click(page.get_by_role("button", name="Create New Quiz"))
        dialog = page.get_by_role("dialog")
        dialog.locator("input[name='title']").fill("Coral Habitats Check")
        dialog.locator("textarea[name='description']").fill("Short reef quiz")
        dialog.locator("select[name='subject_id']").select_option(str(SUBJECT_1_ID))
        dialog.locator("input[name='question_count']").fill("1")
        dialog.locator("input[name='time_limit_minutes']").fill("10")
        dialog.get_by_role("button", name="Save Quiz").click()

        expect(page.get_by_role("status")).to_contain_text(
            "Quiz 'Coral Habitats Check' created successfully."
        )
        expect(page.get_by_text("Coral Habitats Check", exact=True)).to_be_visible()

        # 3. Edit locked quiz (Reef Ecology Quiz has 2 attempts -> structural fields disabled)
        safe_click(page.get_by_role("button", name="Edit Reef Ecology Quiz"))
        dialog = page.get_by_role("dialog")
        expect(dialog.get_by_text("Locked Quiz:")).to_be_visible()
        expect(dialog.locator("select[name='subject_id']")).to_be_disabled()
        expect(dialog.get_by_role("spinbutton", name="Questions to Sample")).to_be_disabled()
        expect(dialog.get_by_role("spinbutton", name="Time Limit (Mins)")).to_be_disabled()

        dialog.locator("input[name='title']").fill("Reef Ecology Quiz (Updated)")
        dialog.get_by_role("button", name="Save Quiz").click()
        expect(page.get_by_role("status")).to_contain_text(
            "Quiz 'Reef Ecology Quiz (Updated)' updated successfully."
        )

        # 4. Activate hidden draft quiz
        safe_click(page.get_by_role("button", name="Activate Sorting Draft Quiz for students"))
        expect(page.get_by_role("status")).to_contain_text("Quiz activated successfully.")

        # 5. Permanently delete unattempted quiz
        page.once("dialog", lambda d: d.accept())
        safe_click(page.get_by_role("button", name="Delete Sorting Draft Quiz"))
        expect(page.get_by_role("status")).to_contain_text(
            "Quiz 'Sorting Draft Quiz' permanently deleted."
        )
        expect(page.get_by_role("tabpanel").get_by_text("Sorting Draft Quiz")).to_have_count(0)

        # 6. Archive quiz that has existing student attempts
        page.once("dialog", lambda d: d.accept())
        safe_click(page.get_by_role("button", name="Archive Reef Ecology Quiz (Updated)"))
        expect(page.get_by_role("status")).to_contain_text(
            "Quiz 'Reef Ecology Quiz (Updated)' archived. Historical student attempts have been preserved."
        )

    def test_manages_question_pool_create_edit_delete_and_views_quiz_stats(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/quiz-management")

        expect(page.get_by_role("heading", name="Quiz Management")).to_be_visible()

        # Switch to Subject Question Pool tab
        safe_click(page.get_by_role("tab", name=re.compile(r"Subject Question Pool")))
        expect(page.get_by_text("Which organism builds coral reefs?")).to_be_visible()

        # Add a new question
        safe_click(page.get_by_role("button", name="Add Question"))
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        dialog.locator("textarea[name='question_text']").fill("What drives ocean tides?")
        dialog.locator("input[name='option_1']").fill("Lunar gravity")
        dialog.locator("input[name='option_2']").fill("Underwater volcanoes")
        dialog.get_by_role("button", name="Save Question").click()

        expect(page.get_by_role("status")).to_contain_text("Question added to subject pool.")
        expect(page.get_by_text("What drives ocean tides?")).to_be_visible()

        # Edit the newly created question
        tides_row = page.locator("tr", has_text="What drives ocean tides?")
        safe_click(tides_row.get_by_role("button", name="Edit question"))
        dialog = page.get_by_role("dialog")
        dialog.locator("textarea[name='question_text']").fill("What primarily drives Earth's ocean tides?")
        dialog.get_by_role("button", name="Save Question").click()

        expect(page.get_by_role("status")).to_contain_text("Question updated successfully.")
        expect(page.get_by_text("What primarily drives Earth's ocean tides?")).to_be_visible()

        # Delete the edited question
        updated_row = page.locator("tr", has_text="What primarily drives Earth's ocean tides?")
        page.once("dialog", lambda d: d.accept())
        safe_click(updated_row.get_by_role("button", name="Delete question"))

        expect(page.get_by_role("status")).to_contain_text("Question removed from active pool.")
        expect(page.get_by_text("What primarily drives Earth's ocean tides?")).to_have_count(0)

        # Switch to Configured Quizzes tab and open Quiz Statistics
        safe_click(page.get_by_role("tab", name=re.compile(r"Configured Quizzes")))
        safe_click(page.locator(f"a[href='/lecturer/quiz/{QUIZ_1_ID}/statistics']"))

        expect(page).to_have_url(re.compile(f"/lecturer/quiz/{QUIZ_1_ID}/statistics$"))
        expect(page.get_by_text("Locked Attempt History")).to_be_visible()
        expect(page.get_by_role("cell", name="80.0%")).to_be_visible()

        # Navigate back to Quiz Management
        safe_click(page.get_by_role("link", name="← Back to Quiz Management"))
        expect(page).to_have_url(re.compile(r"/lecturer/quiz-management$"))


class TestLecturerStudentProgressPage:
    def test_filters_class_list_and_drills_into_student_detail(
        self, page: Page, lecturer_sign_in, lecturer_state
    ):
        page.goto("/lecturer/student-progress")

        expect(page.get_by_role("heading", name="Student Progress & Class Analytics")).to_be_visible()
        expect(page.get_by_text("Sam Student")).to_be_visible()
        expect(page.get_by_text("210 pts")).to_be_visible()

        # Live search filter on class list
        search_box = page.get_by_label("Filter class by name, ID, or course")
        search_box.fill("Unknown Student")
        expect(page.get_by_text("No students match your search criteria.")).to_be_visible()
        search_box.fill("")

        # Drill into Sam Student's history and trajectory chart
        safe_click(page.get_by_role("link", name="View History & Chart"))

        expect(page).to_have_url(re.compile(f"/lecturer/student-progress/{STUDENT_1_ID}$"))
        expect(page.get_by_role("cell", name="Reef Ecology Quiz")).to_be_visible()
        expect(page.locator("#trajectoryChart")).to_be_visible()

        # Navigate back to class list
        safe_click(page.get_by_role("link", name="← Back to Class List"))
        expect(page).to_have_url(re.compile(r"/lecturer/student-progress$"))