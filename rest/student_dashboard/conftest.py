import pytest


@pytest.fixture
def student_session(client):
    with client.session_transaction() as session:
        session["user_id"] = "00000000-0000-4000-8000-000000000001"
        session["role"] = "student"
