from uuid import UUID

from rest.dashboard import leaderboards as leaderboards_module


SUBJECTS = [
    {"subject_id": UUID("00000000-0000-4000-8000-000000000010"), "name": "Mathematics"},
    {"subject_id": UUID("00000000-0000-4000-8000-000000000011"), "name": "Computing"},
]


class TestSubjectLeaderboardsRoute:
    def test_requires_student_login(self, client):
        response = client.get("/leaderboards")

        assert response.status_code == 302
        assert response.headers["Location"] == "/login"

    def test_renders_top_students_for_default_subject(self, client, monkeypatch):
        leaderboard = [
            {
                "user_id": "student-1",
                "first_name": "Ava",
                "last_name": "Morgan",
                "completed_test_count": 3,
                "average_percentage": 92.5,
                "total_points": 450,
            }
        ]
        monkeypatch.setattr(leaderboards_module, "get_active_subjects", lambda: SUBJECTS)
        monkeypatch.setattr(
            leaderboards_module,
            "get_subject_leaderboard",
            lambda subject_id: leaderboard if subject_id == str(SUBJECTS[0]["subject_id"]) else [],
        )
        _login_as_student(client)

        response = client.get("/leaderboards")

        assert response.status_code == 200
        assert b"Subject Leaderboard" in response.data
        assert b"Mathematics" in response.data
        assert b"Ava Morgan" in response.data
        assert b"450" in response.data
        assert b"92.5% average" in response.data
        assert b'name="subject_id"' in response.data
        assert b"selected" in response.data
        assert b'href="/leaderboards"' in response.data

    def test_selected_subject_is_used_for_leaderboard(self, client, monkeypatch):
        selected_id = str(SUBJECTS[1]["subject_id"])
        subject_ids = []
        monkeypatch.setattr(leaderboards_module, "get_active_subjects", lambda: SUBJECTS)
        monkeypatch.setattr(
            leaderboards_module,
            "get_subject_leaderboard",
            lambda subject_id: subject_ids.append(subject_id) or [],
        )
        _login_as_student(client)

        response = client.get(f"/leaderboards?subject_id={selected_id}")

        assert response.status_code == 200
        assert subject_ids == [selected_id]
        assert b"No completed tests for Computing yet." in response.data

    def test_empty_subject_list_shows_empty_state(self, client, monkeypatch):
        monkeypatch.setattr(leaderboards_module, "get_active_subjects", lambda: [])
        monkeypatch.setattr(
            leaderboards_module,
            "get_subject_leaderboard",
            lambda subject_id: (_ for _ in ()).throw(AssertionError("Should not query a missing subject")),
        )
        _login_as_student(client)

        response = client.get("/leaderboards")

        assert response.status_code == 200
        assert b"No subjects available yet." in response.data


def _login_as_student(client):
    with client.session_transaction() as test_session:
        test_session["user_id"] = "student-user-id"
        test_session["role"] = "student"
