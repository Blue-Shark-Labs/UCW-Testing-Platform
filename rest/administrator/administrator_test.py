# To Run: pytest rest/administrator/administrator_test.py

from uuid import UUID

import rest.administrator.administrator as administrator_module
from werkzeug.security import check_password_hash


class TestAdministratorRoutes:
    def test_activate_deactivate_route_accepts_hidden_post_fields(
        self, client, monkeypatch
    ):
        user_id = UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")
        calls = []

        def fake_set_user_disabled(submitted_user_id, is_disabled):
            calls.append((submitted_user_id, is_disabled))
            return True

        monkeypatch.setattr(
            administrator_module,
            "set_user_disabled",
            fake_set_user_disabled,
        )

        deactivate_response = client.post(
            "/administrator/users/activate-deactivate-user",
            data={"userId": str(user_id), "action": "deactivate"},
        )
        activate_response = client.post(
            "/administrator/users/activate-deactivate-user",
            data={"userId": str(user_id), "action": "activate"},
        )

        assert deactivate_response.status_code == 302
        assert activate_response.status_code == 302
        assert calls == [(user_id, True), (user_id, False)]

    def test_view_subjects_route_renders_database_results(
        self, app, monkeypatch
    ):
        monkeypatch.setattr(
            administrator_module,
            "list_subjects",
            lambda search, limit, offset: (
                [{
                    "subjectId": "650e8400-e29b-41d4-a716-446655440001",
                    "name": "Ocean Sciences",
                    "description": "Marine environments",
                    "isActive": True,
                    "lecturerNames": ["Ada Lecturer"],
                }],
                1,
            ),
        )

        with app.test_request_context("/administrator/subjects"):
            response = administrator_module.administrator_view_subjects_route()

        assert "Ocean Sciences" in response
        assert "Ada Lecturer" in response
        assert "Administration Panel" in response

    def test_create_subject_persists_database_fields(self, client, monkeypatch):
        lecturer_id = "8c2c51c3-d847-4d51-8442-f46f814db3c7"
        created = {}
        monkeypatch.setattr(
            administrator_module,
            "list_available_lecturers",
            lambda: [{
                "userId": lecturer_id,
                "firstName": "Ada",
                "lastName": "Lecturer",
            }],
        )

        def fake_create_subject(name, description, lecturer_ids, subject_id):
            created.update(
                name=name,
                description=description,
                lecturer_ids=lecturer_ids,
                subject_id=subject_id,
            )
            return subject_id

        monkeypatch.setattr(
            administrator_module, "create_subject", fake_create_subject
        )

        response = client.post(
            "/administrator/create-subject",
            data={
                "name": "Ocean Sciences",
                "description": "Marine environments",
                "lecturerId": [lecturer_id],
            },
        )

        assert response.status_code == 302
        assert created["name"] == "Ocean Sciences"
        assert created["description"] == "Marine environments"
        assert created["lecturer_ids"] == [UUID(lecturer_id)]
        assert isinstance(created["subject_id"], UUID)

    def test_create_student_user_hashes_password_and_saves_profile(
        self, client, monkeypatch
    ):
        created = {}

        def fake_create_user(*args):
            created["args"] = args
            return UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")

        monkeypatch.setattr(administrator_module, "create_user", fake_create_user)

        response = client.post(
            "/administrator/create-user",
            data={
                "firstName": "Sam",
                "lastName": "Student",
                "email": "sam@example.test",
                "password": "a-local-password",
                "role": "student",
                "studentNumber": "S12345",
                "courseTitle": "Marine Science",
            },
        )

        assert response.status_code == 302
        args = created["args"]
        assert args[0:3] == ("Sam", "Student", "sam@example.test")
        assert args[4:] == ("student", "S12345", "Marine Science")
        assert check_password_hash(args[3], "a-local-password")

    def test_edit_subject_updates_database_and_lecturer_assignment(
        self, client, monkeypatch
    ):
        subject_id = UUID("650e8400-e29b-41d4-a716-446655440001")
        lecturer_id = UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")
        updated = {}

        monkeypatch.setattr(
            administrator_module,
            "get_subject",
            lambda _subject_id: {
                "subjectId": str(subject_id),
                "name": "Ocean Sciences",
                "description": "Marine environments",
                "isActive": True,
                "lecturers": [],
            },
        )
        monkeypatch.setattr(
            administrator_module,
            "list_available_lecturers",
            lambda: [{
                "userId": str(lecturer_id),
                "firstName": "Ada",
                "lastName": "Lecturer",
            }],
        )

        def fake_update_subject(*args):
            updated["args"] = args
            return True

        monkeypatch.setattr(
            administrator_module, "update_subject", fake_update_subject
        )

        response = client.post(
            f"/administrator/edit-subject/{subject_id}",
            data={
                "isActive": "false",
                "name": "Ocean Systems",
                "description": "Updated description",
                "lecturerId": [str(lecturer_id)],
            },
        )

        assert response.status_code == 302
        assert updated["args"] == (
            subject_id,
            "Ocean Systems",
            "Updated description",
            False,
            [lecturer_id],
        )

    def test_user_route_uses_uuid_and_updates_user_in_database(
        self, client, monkeypatch
    ):
        user_id = UUID("8c2c51c3-d847-4d51-8442-f46f814db3c7")
        updated = {}
        monkeypatch.setattr(
            administrator_module,
            "get_user",
            lambda _user_id: {
                "userId": str(user_id),
                "firstName": "Ada",
                "lastName": "Lecturer",
                "email": "ada@example.test",
                "role": "lecturer",
                "isDisabled": True,
                "lastLoginAt": "",
                "studentNumber": "",
                "courseTitle": "",
            },
        )
        def fake_update_user(*args):
            updated["args"] = args
            return True

        monkeypatch.setattr(
            administrator_module, "update_user", fake_update_user
        )

        response = client.post(
            f"/administrator/edit-user/{user_id}",
            data={
                "firstName": "Ada",
                "lastName": "Byron",
                "email": "ada@example.test",
                "role": "admin",
            },
        )

        assert response.status_code == 302
        assert updated["args"] == (
            user_id,
            "Ada",
            "Byron",
            "ada@example.test",
            "admin",
            None,
            None,
        )
