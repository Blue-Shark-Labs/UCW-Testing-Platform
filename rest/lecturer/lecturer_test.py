# To Run: pytest rest/lecturer/lecturer_test.py

from datetime import datetime
from uuid import UUID

import rest.lecturer.student_management as student_mgmt_module
from werkzeug.security import check_password_hash


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

        with app.test_request_context("/lecturer/student-management"):
            html = student_mgmt_module.lecturer_management_route()

        assert "Sam Student" in html
        assert "ID: S0000001" in html
        assert "BSc Computer Science" in html
        assert "Pending Approval" in html

    def test_create_student_hashes_password_and_calls_db(
        self, client, monkeypatch
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

        response = client.post(
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

    def test_edit_student_updates_student_record(self, client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        updated = {}

        def fake_update_student(sid, first_name, last_name, course):
            updated["args"] = (sid, first_name, last_name, course)
            return True

        monkeypatch.setattr(
            student_mgmt_module, "update_student", fake_update_student
        )

        response = client.post(
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

    def test_approve_student_calls_approve(self, client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        approved = []
        monkeypatch.setattr(
            student_mgmt_module,
            "approve_student",
            lambda sid: approved.append(sid) or True,
        )

        response = client.post(f"/lecturer/approve-student/{student_id}")

        assert response.status_code == 302
        assert approved == [student_id]

    def test_toggle_student_status_calls_toggle(self, client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        toggled = []
        monkeypatch.setattr(
            student_mgmt_module,
            "toggle_student_status",
            lambda sid: toggled.append(sid) or True,
        )

        response = client.post(f"/lecturer/toggle-student-status/{student_id}")

        assert response.status_code == 302
        assert toggled == [student_id]

    def test_delete_student_handles_existing_attempts(self, client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        monkeypatch.setattr(
            student_mgmt_module,
            "delete_student",
            lambda sid: ("has_attempts", None),
        )

        response = client.post(f"/lecturer/student/{student_id}/delete")
        assert response.status_code == 302

    def test_delete_student_deletes_user_when_no_attempts(self, client, monkeypatch):
        student_id = UUID("1cf03c86-74c1-4da8-b411-c6d62c64da70")
        monkeypatch.setattr(
            student_mgmt_module,
            "delete_student",
            lambda sid: ("deleted", ("Sam", "Student")),
        )

        response = client.post(f"/lecturer/student/{student_id}/delete")
        assert response.status_code == 302