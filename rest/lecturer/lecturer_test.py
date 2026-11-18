# To Run: pytest rest/lecturer/lecturer_test.py

from datetime import datetime
from uuid import UUID

import psycopg
import pytest
from werkzeug.security import check_password_hash

import rest.lecturer.student_management as student_mgmt_module


class FakeCursor:
    """Simulates a psycopg cursor with scripted fetchone/fetchall responses."""

    def __init__(self, fetchone_results=None, fetchall_results=None, error=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.error = error
        self.executed = []

    def execute(self, query, params=None):
        if self.error:
            raise self.error
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeConnectionProvider:
    def __init__(self, fake_cursor):
        self._cursor = fake_cursor

    def cursor(self):
        return self._cursor


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
        fake_cur = FakeCursor(fetchall_results=[rows])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
        )

        with app.test_request_context("/lecturer/student-management"):
            html = student_mgmt_module.lecturer_management_route()

        assert "Sam Student" in html
        assert "ID: S0000001" in html
        assert "BSc Computer Science" in html
        assert "Pending Approval" in html

    def test_create_student_hashes_password_and_generates_student_number(
        self, client, monkeypatch
    ):
        new_user_id = UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")
        fake_cur = FakeCursor(fetchone_results=[(new_user_id,), ("S0000003",)])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
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
        assert len(fake_cur.executed) == 2

        # Verify user insert & password hashing
        user_query, user_params = fake_cur.executed[0]
        assert "INSERT INTO users" in user_query
        assert user_params[0:3] == ("Jane", "Doe", "j.doe@ucw.ac.uk")
        assert check_password_hash(user_params[3], "Student123!")

        # Verify student profile insert uses student_number_seq
        student_query, student_params = fake_cur.executed[1]
        assert "student_number_seq" in student_query
        assert student_params == (new_user_id, "Computer Science")

    def test_edit_student_updates_user_and_upserts_student_profile(
        self, client, monkeypatch
    ):
        student_id = "1cf03c86-74c1-4da8-b411-c6d62c64da70"
        fake_cur = FakeCursor(fetchone_results=[(UUID(student_id),)])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
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
        assert len(fake_cur.executed) == 2
        assert fake_cur.executed[0][1] == ("Samuel", "Student", student_id)
        assert "ON CONFLICT (user_id)" in fake_cur.executed[1][0]
        assert fake_cur.executed[1][1] == (student_id, "Software Engineering")

    def test_approve_student_sets_is_approved_true(self, client, monkeypatch):
        student_id = "1cf03c86-74c1-4da8-b411-c6d62c64da70"
        fake_cur = FakeCursor(fetchone_results=[(UUID(student_id),)])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
        )

        response = client.post(f"/lecturer/approve-student/{student_id}")

        assert response.status_code == 302
        query, params = fake_cur.executed[0]
        assert "SET is_approved = TRUE" in query
        assert params == (student_id,)

    def test_toggle_student_status_flips_is_disabled(self, client, monkeypatch):
        student_id = "1cf03c86-74c1-4da8-b411-c6d62c64da70"
        fake_cur = FakeCursor(fetchone_results=[(True,)])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
        )

        response = client.post(f"/lecturer/toggle-student-status/{student_id}")

        assert response.status_code == 302
        query, params = fake_cur.executed[0]
        assert "SET is_disabled = NOT is_disabled" in query
        assert params == (student_id,)

    def test_delete_student_blocks_deletion_when_test_attempts_exist(
        self, client, monkeypatch
    ):
        student_id = "1cf03c86-74c1-4da8-b411-c6d62c64da70"
        fake_cur = FakeCursor(fetchone_results=[(True,)])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
        )

        response = client.post(f"/lecturer/student/{student_id}/delete")

        assert response.status_code == 302
        # Only the EXISTS check runs; DELETE FROM users must not execute
        assert len(fake_cur.executed) == 1
        assert "FROM test_attempts" in fake_cur.executed[0][0]

    def test_delete_student_deletes_user_when_no_attempts_exist(
        self, client, monkeypatch
    ):
        student_id = "1cf03c86-74c1-4da8-b411-c6d62c64da70"
        fake_cur = FakeCursor(fetchone_results=[(False,), ("Sam", "Student")])
        monkeypatch.setattr(
            student_mgmt_module,
            "PostgresConnectionProvider",
            lambda: FakeConnectionProvider(fake_cur),
        )

        response = client.post(f"/lecturer/student/{student_id}/delete")

        assert response.status_code == 302
        assert len(fake_cur.executed) == 2
        assert "DELETE FROM users" in fake_cur.executed[1][0]
        assert fake_cur.executed[1][1] == (student_id,)