# To Run: pytest rest/lecturer/lecturer_test.py

from datetime import datetime
from uuid import UUID

import pytest
import rest.lecturer.quiz_management as quiz_mgmt_module
import rest.lecturer.student_management as student_mgmt_module
import rest.lecturer.view_subjects as view_subjects_module
from werkzeug.security import check_password_hash


@pytest.fixture(autouse=True)
def stub_session_user_db(monkeypatch):
    """Prevent load_session_user() in rest/router.py from hitting PostgreSQL during unit tests."""
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return ("Test", "Lecturer", "lecturer")

    class FakeConnectionProvider:
        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)


@pytest.fixture
def lecturer_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "11111111-1111-1111-1111-111111111111"
        sess["role"] = "lecturer"
    return client


class TestLecturerAuthorization:
    def test_lecturer_routes_redirect_anonymous_users_to_login(self, client):
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/lecturer/student-management")

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    def test_lecturer_routes_forbid_database_non_lecturer_even_if_session_says_lecturer(
        self, client, monkeypatch
    ):
        """FR-83: Database role claim overrides spoofed session role and returns HTTP 403."""
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return ("Test", "Student", "student")

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)
        with client.session_transaction() as sess:
            sess["user_id"] = "11111111-1111-1111-1111-111111111111"
            sess["role"] = "lecturer"

        response = client.get("/lecturer/student-management")

        assert response.status_code == 403

    def test_lecturer_routes_forbid_session_for_user_missing_from_database(
        self, client, monkeypatch
    ):
        """FR-83: Session referencing a missing/deleted user returns HTTP 403."""
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return None

        class FakeConnectionProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr("rest.router.PostgresConnectionProvider", FakeConnectionProvider)
        with client.session_transaction() as sess:
            sess["user_id"] = "11111111-1111-1111-1111-111111111111"
            sess["role"] = "lecturer"

        response = client.post(
            "/lecturer/approve-student/1cf03c86-74c1-4da8-b411-c6d62c64da70"
        )

        assert response.status_code == 403


class TestLecturerStudentManagementRoutes:
    def test_student_management_renders_student_number_and_statuses(
        self, app, monkeypatch
    ):
        user_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        rows = [
            (
                user_id,
                "Sam",
                "Student",
                "student@dev.local",
                datetime(2026, 11, 18, 9, 0),
                False,
                "S0000001",
                "BSc Computer Science",
                True,
            ),
            (
                UUID("9e80f93c-ea42-4348-8a25-dc54a68be6d2"),
                "Alex",
                "Pending",
                "alex@dev.local",
                None,
                False,
                "S0000002",
                "BSc Computing",
                False,
            ),
        ]
        monkeypatch.setattr(student_mgmt_module, "list_students", lambda: rows)
        monkeypatch.setattr(student_mgmt_module, "get_class_progress_summary", lambda: [])

        with app.test_request_context("/lecturer/student-management"):
            html = student_mgmt_module.lecturer_management_route()

        assert "Sam Student" in html
        assert "ID: S0000001" in html
        assert "BSc Computer Science" in html
        assert "Pending Approval" in html
        assert "Reject" in html

    def test_create_student_hashes_password_and_calls_db(
        self, lecturer_client, monkeypatch
    ):
        created = {}

        def fake_create_student(first_name, last_name, email, password_hash, course):
            created.update(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
                course=course,
            )
            return "S0000003"

        monkeypatch.setattr(
            student_mgmt_module, "create_student", fake_create_student
        )

        response = lecturer_client.post(
            "/lecturer/student/create",
            data={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "J.Doe@ucw.ac.uk",
                "course": "Computer Science",
                "password": "Student123!",
            },
        )

        assert response.status_code == 302
        assert created["first_name"] == "Jane"
        assert created["last_name"] == "Doe"
        assert created["email"] == "j.doe@ucw.ac.uk"
        assert created["course"] == "Computer Science"
        assert check_password_hash(created["password_hash"], "Student123!")

    def test_edit_student_updates_student_record(self, lecturer_client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        updated = {}

        def fake_update_student(sid, first_name, last_name, course):
            updated["args"] = (sid, first_name, last_name, course)
            return True

        monkeypatch.setattr(
            student_mgmt_module, "update_student", fake_update_student
        )

        response = lecturer_client.post(
            f"/lecturer/student/{student_id}/edit",
            data={
                "first_name": "Samuel",
                "last_name": "Student",
                "course": "Software Engineering",
            },
        )

        assert response.status_code == 302
        assert updated["args"] == (
            student_id,
            "Samuel",
            "Student",
            "Software Engineering",
        )

    def test_approve_student_calls_approve_and_sends_notification_email(
        self, lecturer_client, monkeypatch
    ):
        """FR-56 & FR-57: Approving a student activates their account and dispatches email."""
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        approved = []
        emailed = []

        monkeypatch.setattr(
            student_mgmt_module,
            "approve_student",
            lambda sid: approved.append(sid) or {
                "email": "sam@dev.local",
                "first_name": "Sam",
                "last_name": "Student",
            },
        )
        monkeypatch.setattr(
            student_mgmt_module,
            "send_student_approval_email",
            lambda email, first_name: emailed.append((email, first_name)) or True,
        )

        response = lecturer_client.post(f"/lecturer/approve-student/{student_id}")

        assert response.status_code == 302
        assert approved == [student_id]
        assert emailed == [("sam@dev.local", "Sam")]

    def test_reject_student_declines_pending_registration(
        self, lecturer_client, monkeypatch
    ):
        """FR-56: Lecturer can reject a pending student registration."""
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        rejected = []

        monkeypatch.setattr(
            student_mgmt_module,
            "reject_student",
            lambda sid: rejected.append(sid) or ("rejected", ("Alex", "Pending")),
        )

        response = lecturer_client.post(f"/lecturer/reject-student/{student_id}")

        assert response.status_code == 302
        assert rejected == [student_id]

    def test_toggle_student_status_calls_toggle(self, lecturer_client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        toggled = []
        monkeypatch.setattr(
            student_mgmt_module,
            "toggle_student_status",
            lambda sid: toggled.append(sid) or True,
        )

        response = lecturer_client.post(f"/lecturer/toggle-student-status/{student_id}")

        assert response.status_code == 302
        assert toggled == [student_id]

    def test_delete_student_anonymises_when_existing_attempts(
        self, lecturer_client, monkeypatch
    ):
        """NFR-05: Terminating a student with attempts anonymises PII in GDPR compliance."""
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        monkeypatch.setattr(
            student_mgmt_module,
            "delete_student",
            lambda sid: ("anonymised", ("Sam", "Student")),
        )

        response = lecturer_client.post(f"/lecturer/student/{student_id}/delete")
        assert response.status_code == 302

    def test_delete_student_deletes_user_when_no_attempts(
        self, lecturer_client, monkeypatch
    ):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        monkeypatch.setattr(
            student_mgmt_module,
            "delete_student",
            lambda sid: ("deleted", ("Sam", "Student")),
        )

        response = lecturer_client.post(f"/lecturer/student/{student_id}/delete")
        assert response.status_code == 302

    def test_student_progress_class_list_and_detail_history_and_chart(
        self, lecturer_client, monkeypatch
    ):
        """FR-63, FR-64, FR-65: Aggregate class list, detailed test history, and trajectory chart."""
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")

        class_summary = [
            {
                "student_id": str(student_id),
                "first_name": "Sam",
                "last_name": "Student",
                "name": "Sam Student",
                "email": "sam@dev.local",
                "student_number": "S0000001",
                "course_title": "BSc Computer Science",
                "completed_tests": 2,
                "cumulative_points": 210,
                "average_percentage": 85.0,
            }
        ]
        monkeypatch.setattr(
            student_mgmt_module, "get_class_progress_summary", lambda: class_summary
        )

        # FR-63: Aggregate class view
        list_resp = lecturer_client.get("/lecturer/student-progress")
        assert list_resp.status_code == 200
        assert b"Sam Student" in list_resp.data
        assert b"210 pts" in list_resp.data
        assert b"85.0%" in list_resp.data

        # FR-64 & FR-65: Detailed student history & visual trajectory chart
        attempt_entry = {
            "attempt_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "test_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "test_name": "Algorithms Midterm",
            "subject_name": "Computer Science",
            "completed_at": datetime(2026, 11, 20, 14, 30),
            "completed_date_str": "20 Nov 2026, 14:30",
            "short_date_str": "20 Nov",
            "question_count": 10,
            "percentage": 85.0,
            "total_points": 210,
        }
        monkeypatch.setattr(
            student_mgmt_module,
            "get_student_progress_detail",
            lambda sid: {
                "student": class_summary[0],
                "trajectory": [attempt_entry],
                "history": [attempt_entry],
            },
        )

        detail_resp = lecturer_client.get(f"/lecturer/student-progress/{student_id}")
        assert detail_resp.status_code == 200
        assert b"Algorithms Midterm" in detail_resp.data
        assert b"20 Nov 2026, 14:30" in detail_resp.data
        assert b"trajectoryChart" in detail_resp.data

    def test_delete_student_db_anonymises_email_within_varchar_50(self, monkeypatch):
        """NFR-05: Anonymised email fits users.email VARCHAR(50) and matches exclusion filter."""
        import database.lecturer.students as students_db

        student_id = UUID("4b643816-c5e5-4b0d-b2b5-a8a50542eb8f")
        executed = []

        class FakeCursor:
            def __init__(self):
                self.step = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, query, params=None):
                executed.append((query, params))

            def fetchone(self):
                self.step += 1
                if self.step == 1:
                    return ("Farah", "Ahmed")
                if self.step == 2:
                    return (True,)
                return None

        class FakeProvider:
            def cursor(self):
                return FakeCursor()

        monkeypatch.setattr(students_db, "PostgresConnectionProvider", FakeProvider)

        outcome, original_name = students_db.delete_student(student_id)

        assert outcome == "anonymised"
        assert original_name == ("Farah", "Ahmed")
        user_update_params = executed[3][1]
        anonymised_email = user_update_params[0]
        assert len(anonymised_email) <= 50
        assert anonymised_email.startswith("deleted_")
        assert anonymised_email.endswith("@anonymised.local")

class TestLecturerQuizManagementRoutes:
    def test_quiz_management_renders_quizzes_and_question_pool(self, app, monkeypatch):
        subject_id = "650e8400-e29b-41d4-a716-446655440001"
        monkeypatch.setattr(
            quiz_mgmt_module,
            "list_quizzes",
            lambda: [
                {
                    "test_id": "22222222-2222-2222-2222-222222222222",
                    "subject_id": subject_id,
                    "subject_name": "Marine Biology",
                    "title": "Reef Ecology Quiz",
                    "description": "Introductory coral reef assessment",
                    "question_count": 5,
                    "time_limit_minutes": 20,
                    "is_active": True,
                    "attempt_count": 3,
                }
            ],
        )
        monkeypatch.setattr(
            quiz_mgmt_module,
            "list_subjects_with_pool_counts",
            lambda: [
                {
                    "subject_id": subject_id,
                    "name": "Marine Biology",
                    "is_active": True,
                    "question_count": 12,
                }
            ],
        )
        monkeypatch.setattr(
            quiz_mgmt_module,
            "list_questions",
            lambda: [
                {
                    "question_id": "33333333-3333-3333-3333-333333333333",
                    "subject_id": subject_id,
                    "subject_name": "Marine Biology",
                    "question_text": "Which organism builds coral reefs?",
                    "options": [
                        {"option_id": "44444444-4444-4444-4444-444444444444", "option_text": "Stony corals", "is_correct": True},
                        {"option_id": "55555555-5555-5555-5555-555555555555", "option_text": "Kelp", "is_correct": False},
                    ],
                }
            ],
        )

        with app.test_request_context("/lecturer/quiz-management"):
            html = quiz_mgmt_module.quiz_management_route()

        assert "Reef Ecology Quiz" in html
        assert "Marine Biology" in html
        assert "20 mins" in html
        assert "Locked" in html
        assert "Stats" in html
        assert "Which organism builds coral reefs?" in html

    def test_quiz_statistics_route_renders_summary_and_attempts(
        self, lecturer_client, monkeypatch
    ):
        """FR-75: Contextual view statistics action displays quiz analytics."""
        test_id = UUID("22222222-2222-2222-2222-222222222222")
        monkeypatch.setattr(
            quiz_mgmt_module,
            "get_quiz_statistics",
            lambda tid: {
                "quiz": {
                    "test_id": str(test_id),
                    "title": "Reef Ecology Quiz",
                    "description": "Introductory coral reef assessment",
                    "subject_name": "Marine Biology",
                    "question_count": 5,
                    "time_limit_minutes": 20,
                    "is_active": True,
                },
                "summary": {
                    "completed_count": 1,
                    "avg_percentage": 80.0,
                    "avg_points": 110.0,
                    "highest_percentage": 80.0,
                    "lowest_percentage": 80.0,
                },
                "attempts": [
                    {
                        "attempt_id": "99999999-9999-9999-9999-999999999999",
                        "student_name": "Sam Student",
                        "student_number": "S0000001",
                        "completed_at": "22 Nov 2026, 10:15",
                        "percentage": 80.0,
                        "total_points": 110,
                    }
                ],
            },
        )

        response = lecturer_client.get(f"/lecturer/quiz/{test_id}/statistics")
        assert response.status_code == 200
        assert b"Reef Ecology Quiz" in response.data
        assert b"Locked Attempt History" in response.data
        assert b"Sam Student" in response.data
        assert b"80.0%" in response.data

    def test_create_question_validates_and_calls_db(self, lecturer_client, monkeypatch):
        subject_id = UUID("650e8400-e29b-41d4-a716-446655440001")
        created = {}

        def fake_create_question(sid, text, options):
            created.update(subject_id=sid, question_text=text, options=options)
            return UUID("33333333-3333-3333-3333-333333333333")

        monkeypatch.setattr(quiz_mgmt_module, "create_question", fake_create_question)

        response = lecturer_client.post(
            "/lecturer/question/create",
            data={
                "subject_id": str(subject_id),
                "question_text": "What is the primary driver of ocean tides?",
                "option_1": "Lunar gravity",
                "option_2": "Underwater volcanoes",
                "option_3": "Trade winds",
                "option_4": "",
                "correct_option": "1",
            },
        )

        assert response.status_code == 302
        assert created["subject_id"] == subject_id
        assert created["question_text"] == "What is the primary driver of ocean tides?"
        assert created["options"] == [
            ("Lunar gravity", True),
            ("Underwater volcanoes", False),
            ("Trade winds", False),
        ]

    def test_create_quiz_calls_db_with_parsed_fields(self, lecturer_client, monkeypatch):
        subject_id = UUID("650e8400-e29b-41d4-a716-446655440001")
        created = {}

        def fake_create_quiz(**kwargs):
            created.update(kwargs)
            return UUID("22222222-2222-2222-2222-222222222222")

        monkeypatch.setattr(quiz_mgmt_module, "create_quiz", fake_create_quiz)

        response = lecturer_client.post(
            "/lecturer/quiz/create",
            data={
                "title": "Oceanography Basics",
                "description": "Week 1 check",
                "subject_id": str(subject_id),
                "question_count": "5",
                "time_limit_minutes": "",
            },
        )

        assert response.status_code == 302
        assert created["title"] == "Oceanography Basics"
        assert created["subject_id"] == subject_id
        assert created["question_count"] == 5
        assert created["time_limit_minutes"] is None

    def test_toggle_quiz_status_calls_db(self, lecturer_client, monkeypatch):
        test_id = UUID("22222222-2222-2222-2222-222222222222")
        toggled = []
        monkeypatch.setattr(
            quiz_mgmt_module,
            "toggle_quiz_status",
            lambda tid: toggled.append(tid) or False,
        )

        response = lecturer_client.post(f"/lecturer/quiz/{test_id}/toggle-status")

        assert response.status_code == 302
        assert toggled == [test_id]

    def test_delete_quiz_passes_confirmation_flag(self, lecturer_client, monkeypatch):
        test_id = UUID("22222222-2222-2222-2222-222222222222")
        calls = []

        def fake_delete_quiz(tid, confirmed):
            calls.append((tid, confirmed))
            return "archived", "Reef Ecology Quiz"

        monkeypatch.setattr(quiz_mgmt_module, "delete_quiz", fake_delete_quiz)

        response = lecturer_client.post(
            f"/lecturer/quiz/{test_id}/delete",
            data={"confirmed": "true"},
        )

        assert response.status_code == 302
        assert calls == [(test_id, True)]

class TestLecturerSubjectsRoutes:
    def test_view_subjects_renders_assigned_subjects(self, lecturer_client, monkeypatch):
        monkeypatch.setattr(
            view_subjects_module,
            "list_lecturer_subjects",
            lambda lecturer_id, search="": [
                {
                    "subject_id": "650e8400-e29b-41d4-a716-446655440001",
                    "name": "Marine Biology",
                    "description": "Coral reef and ocean ecosystems",
                    "is_active": True,
                    "lecturer_names": ["Test Lecturer"],
                    "question_count": 14,
                    "quiz_count": 2,
                }
            ],
        )

        response = lecturer_client.get("/lecturer/subjects")
        assert response.status_code == 200
        assert b"My Subjects" in response.data
        assert b"Marine Biology" in response.data
        assert b"14 questions" in response.data
        assert b"2 quizzes" in response.data